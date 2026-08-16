#!/usr/bin/env python3
"""
concept_agent.py — 主動發現 LLM-Wiki 中語意接近但從未連結的跨域卡片對

原理：
  1. 從 ChromaDB 讀取所有卡片的 embedding 向量
  2. 計算 cosine similarity 矩陣（numpy，快速）
  3. 排除已有 wikilink 的對（known connection）
  4. 找到 similarity 在甜蜜區間 [SIM_LOW, SIM_HIGH] 的跨域對
  5. 輸出 JSON 供 Claude 合成「你沒想到的連結」報告

Usage:
  python3 concept_agent.py [--top N] [--sim-low 0.55] [--sim-high 0.82]

Output: JSON to stdout
"""

import os
import re
import json
import argparse
import sqlite3
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print(json.dumps({"error": "numpy not installed: pip install numpy"}))
    exit(1)

try:
    import chromadb
except ImportError:
    print(json.dumps({"error": "chromadb not installed: pip install chromadb"}))
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from google import genai as google_genai

VAULT_ROOT = Path("/Users/jeffliu/Documents/A05_Obsidian Vault")
WIKI_DIR   = VAULT_ROOT / "300 LLM-Wiki"
INDEX_DIR  = WIKI_DIR / ".ai_index"
DB_DIR     = INDEX_DIR / "chroma_db"
GRAPH_DB   = INDEX_DIR / "wiki_graph.db"

# --- Domain detection via filename keywords ---
DOMAIN_KEYWORDS = {
    "telecom":       ["AI-RAN", "O-RAN", "OCUDU", "xPON", "Fronthaul", "DeepSig", "OmniPHY",
                      "IOWN", "AI in RAN", "5G NR", "6G", "FWA", "ISAC", "Neural Receiver",
                      "通訊", "電信", "基站", "頻寬", "VALOR", "mMIMO", "xHaul",
                      "APN", "DTC", "RIC ", "OCUDU", " RAN "],
    "parenting":     ["孩子", "教養", "Parenting", "女兒", "情緒調節", "修復力", "親子", "Good Inside"],
    "leadership":    ["領導", "管理", "Leadership", "變革", "授權", "ADKAR", "員工", "團隊",
                      "組織", "BART"],
    "personal-growth": ["自我", "孤獨", "修行", "情商", "韌性", "Resilience",
                        "閾值", "自覺", "覺察", "Fluid Identity", "孤獨閾值", "修行"],
    "business":      ["商業", "供應鏈", "ODM", "市場", "策略", "Business", "Strategy",
                      "降維", "競爭", "消費", "品牌", "商業模式", "財富"],
    "ai-tools":      ["LLM", "Agent", "Coding", "PRD", "Vibe", "ChatGPT", "Claude",
                      "Prompt", "RAG", "自動化", "AI 協作", "AI 世代", "GateLynch",
                      "WikiAgent", "concept_agent"],
    "cognition":     ["認知", "思維", "學習", "閱讀", "費曼", "Feynman", "心智", "框架",
                      "抽象", "後設認知", "注意力"],
    "philosophy":    ["哲學", "意義", "道德", "倫理", "靈光", "道德經", "幸福", "人生意義"],
}

def detect_domain(filename: str) -> str:
    fn = filename
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in fn.lower():
                return domain
    return "other"


def extract_wikilinks(md_path: Path) -> set:
    """Extract [[wikilink]] targets from a .md file."""
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception:
        return set()
    raw = re.findall(r'\[\[([^\]|#\n]+?)(?:[|#][^\]]*)?\]\]', content)
    return {link.strip() for link in raw}


def cosine_sim_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute full cosine similarity matrix from row-wise embedding matrix."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-10, norms)
    normed = embeddings / norms
    return normed @ normed.T


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top",      type=int,   default=15,   help="Number of pairs to return")
    parser.add_argument("--sim-low",  type=float, default=0.55, help="Minimum similarity threshold")
    parser.add_argument("--sim-high", type=float, default=0.82, help="Maximum similarity threshold")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(json.dumps({"error": "GEMINI_API_KEY not set"}))
        exit(1)

    if not DB_DIR.exists():
        print(json.dumps({"error": "ChromaDB not found. Run /ingest first."}))
        exit(1)

    # --- Load embeddings from ChromaDB ---
    # We only need stored vectors (.get), so no embedding function needed at open time.
    for attempt in range(3):
        try:
            settings = chromadb.config.Settings(anonymized_telemetry=False)
            chroma_client = chromadb.PersistentClient(path=str(DB_DIR), settings=settings)
            collection = chroma_client.get_collection(name="llm_wiki_cards")
            break
        except Exception as e:
            if attempt == 2:
                print(json.dumps({"error": f"Cannot open ChromaDB collection after 3 attempts: {e}"}))
                exit(1)
            import time; time.sleep(2)

    count = collection.count()
    if count < 2:
        print(json.dumps({"error": f"Not enough cards ({count}) to find connections."}))
        exit(1)

    # Fetch all cards: ids + embeddings + metadatas
    all_data = collection.get(include=["embeddings", "metadatas"])
    ids        = all_data["ids"]          # list of filenames (stems)
    embeddings = np.array(all_data["embeddings"], dtype=np.float32)
    metadatas  = all_data["metadatas"]

    n = len(ids)

    # --- Build wikilink adjacency set (already-known connections) ---
    # ChromaDB IDs already include ".md" suffix; use directly as filenames.
    id_to_idx = {card_id.lower(): idx for idx, card_id in enumerate(ids)}

    linked_pairs = set()
    for i, card_id in enumerate(ids):
        md_file = WIKI_DIR / card_id  # card_id already has .md
        if not md_file.exists():
            md_file = WIKI_DIR / f"{card_id}.md"  # fallback
        if md_file.exists():
            links = extract_wikilinks(md_file)
            for link in links:
                # wikilinks don't include .md; try both forms
                target_key = link.lower() + ".md"
                j = id_to_idx.get(target_key) or id_to_idx.get(link.lower())
                if j is not None and i != j:
                    linked_pairs.add((min(i, j), max(i, j)))

    # --- Compute similarity matrix ---
    sim_matrix = cosine_sim_matrix(embeddings)

    # --- Collect candidate pairs ---
    candidates = []
    for i in range(n):
        domain_i = detect_domain(ids[i])
        for j in range(i + 1, n):
            if (i, j) in linked_pairs:
                continue
            sim = float(sim_matrix[i, j])
            if args.sim_low <= sim <= args.sim_high:
                domain_j = detect_domain(ids[j])
                cross_domain = domain_i != domain_j and domain_i != "other" and domain_j != "other"
                candidates.append({
                    "card_a": ids[i],
                    "card_b": ids[j],
                    "domain_a": domain_i,
                    "domain_b": domain_j,
                    "similarity": round(sim, 4),
                    "cross_domain": cross_domain,
                })

    # Sort: cross-domain pairs first, then by similarity descending
    candidates.sort(key=lambda x: (-int(x["cross_domain"]), -x["similarity"]))

    top_pairs = candidates[:args.top]

    # --- Domain distribution ---
    domain_counts: dict = {}
    for card_id in ids:
        d = detect_domain(card_id)
        domain_counts[d] = domain_counts.get(d, 0) + 1

    # --- Cards with fewest wikilink connections (structural orphans) ---
    # Count how many times each card appears as a link target across all cards.
    inbound_links: dict = {card_id: 0 for card_id in ids}
    for i, card_id in enumerate(ids):
        md_file = WIKI_DIR / card_id
        if not md_file.exists():
            md_file = WIKI_DIR / f"{card_id}.md"
        if md_file.exists():
            links = extract_wikilinks(md_file)
            for link in links:
                target_key = link.lower() + ".md"
                matched = id_to_idx.get(target_key) or id_to_idx.get(link.lower())
                if matched is not None:
                    inbound_links[ids[matched]] = inbound_links.get(ids[matched], 0) + 1

    orphan_scores = [(card_id, inbound_links.get(card_id, 0)) for card_id in ids]
    orphan_scores.sort(key=lambda x: x[1])
    isolated_cards = [
        {"card": card_id, "domain": detect_domain(card_id), "inbound_links": count}
        for card_id, count in orphan_scores[:5]
    ]

    result = {
        "total_cards": n,
        "total_pairs_checked": n * (n - 1) // 2,
        "already_linked_pairs": len(linked_pairs),
        "candidate_pairs": len(candidates),
        "top_pairs": top_pairs,
        "domain_distribution": domain_counts,
        "isolated_cards": isolated_cards,
        "sim_range": [args.sim_low, args.sim_high],
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
