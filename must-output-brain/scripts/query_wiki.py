#!/usr/bin/env python3
"""
query_wiki.py — LLM-Wiki 語意搜尋 + wikilink traversal

Usage:
  python3 query_wiki.py "<question>" [--top N] [--deep]

Output: JSON with relevant wiki page paths for Claude to read and synthesize.
"""

import os
import sys
import json
import re
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

VAULT_ROOT = Path("/Users/jeffliu/Documents/A05_Obsidian Vault")
WIKI_DIR   = VAULT_ROOT / "300 LLM-Wiki"
INDEX_DIR  = WIKI_DIR / ".ai_index"
DB_DIR     = INDEX_DIR / "chroma_db"
GRAPH_DB   = INDEX_DIR / "wiki_graph.db"


def extract_wikilinks(content: str) -> list:
    """Extract [[wikilink]] targets from markdown, ignoring anchors and aliases."""
    raw = re.findall(r'\[\[([^\]|#\n]+?)(?:[|#][^\]]*)?\]\]', content)
    return [link.strip() for link in raw if link.strip()]


def resolve_wikilink(link_name: str) -> Path:
    """Find the wiki .md file matching a wikilink name. Returns None if not found."""
    # Exact match
    exact = WIKI_DIR / f"{link_name}.md"
    if exact.exists():
        return exact
    # Case-insensitive fallback
    for f in WIKI_DIR.glob("*.md"):
        if f.stem.lower() == link_name.lower():
            return f
    return None


def query_chromadb(question: str, top_n: int):
    """Query ChromaDB with the same embedding function used at index time."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        from google import genai as google_genai
    except ImportError as e:
        return None, f"Missing dependency: {e}"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY not set"

    if not DB_DIR.exists():
        return None, "ChromaDB index not found. Run /ingest on some pages first."

    class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
        def __init__(self, key, model="models/gemini-embedding-2"):
            self.client = google_genai.Client(api_key=key)
            self.model_name = model

        def __call__(self, input):
            response = self.client.models.embed_content(
                model=self.model_name, contents=input
            )
            return [e.values for e in response.embeddings]

        def name(self):
            return "GeminiEmbeddingFunction"

    try:
        client = chromadb.PersistentClient(path=str(DB_DIR))
        collection = client.get_collection(
            name="llm_wiki_cards",
            embedding_function=GeminiEmbeddingFunction(key=api_key),
        )
    except Exception as e:
        return None, f"Cannot open collection: {e}"

    count = collection.count()
    if count == 0:
        return None, "Wiki index is empty."

    results = collection.query(
        query_texts=[question],
        n_results=min(top_n, count),
        include=["metadatas", "distances"],
    )
    return results, None


def query_graph(entities: list) -> list:
    """Query SQLite knowledge graph for entity relationships."""
    if not GRAPH_DB.exists() or not entities:
        return []
    conn = sqlite3.connect(str(GRAPH_DB))
    cursor = conn.cursor()
    edges = []
    for entity in entities[:3]:  # limit to first 3 keywords
        cursor.execute(
            "SELECT subject, predicate, object, source_file FROM graph_edges "
            "WHERE subject LIKE ? OR object LIKE ? LIMIT 5",
            (f"%{entity}%", f"%{entity}%"),
        )
        for row in cursor.fetchall():
            edges.append({"subject": row[0], "predicate": row[1],
                          "object": row[2], "source": row[3]})
    conn.close()
    return edges


def build_page_list(results, question: str, deep: bool) -> tuple:
    """Build hit pages + wikilink traversal neighbors. Returns (pages, hit_count)."""
    hit_pages = []
    visited = set()

    for i, meta in enumerate(results["metadatas"][0]):
        rel_path = meta.get("path", "")
        abs_path = WIKI_DIR / rel_path
        if abs_path.exists():
            distance = results["distances"][0][i]
            str_path = str(abs_path)
            if str_path not in visited:
                visited.add(str_path)
                hit_pages.append({
                    "path": str_path,
                    "filename": meta.get("filename", abs_path.name),
                    "relevance_score": round(1 - distance, 3),
                    "layer": "hit",
                })

    hit_count = len(hit_pages)
    neighbor_pages = []
    depth = 2 if deep else 1
    queue = [p["path"] for p in hit_pages]

    for layer in range(depth):
        next_queue = []
        for page_path_str in queue:
            page_path = Path(page_path_str)
            if not page_path.exists():
                continue
            content = page_path.read_text(encoding="utf-8")
            for link in extract_wikilinks(content):
                resolved = resolve_wikilink(link)
                if resolved and str(resolved) not in visited:
                    visited.add(str(resolved))
                    neighbor_pages.append({
                        "path": str(resolved),
                        "filename": resolved.name,
                        "relevance_score": None,
                        "layer": f"neighbor-{layer + 1}",
                        "via": page_path.name,
                        "link_name": link,
                    })
                    next_queue.append(str(resolved))
        queue = next_queue

    return hit_pages + neighbor_pages, hit_count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Query LLM-Wiki")
    parser.add_argument("question", nargs="+", help="Question to search")
    parser.add_argument("--top", type=int, default=5, help="Top N hits (default: 5)")
    parser.add_argument("--deep", action="store_true", help="2-layer traversal")
    args = parser.parse_args()

    question = " ".join(args.question)

    results, error = query_chromadb(question, args.top)
    if error:
        print(json.dumps({"error": error}, ensure_ascii=False))
        sys.exit(1)

    pages, hit_count = build_page_list(results, question, args.deep)

    # Graph edges for context
    keywords = [w for w in re.split(r"\s+", question) if len(w) > 1]
    graph_edges = query_graph(keywords)

    output = {
        "question": question,
        "traversal_depth": 2 if args.deep else 1,
        "total_pages": len(pages),
        "hit_count": hit_count,
        "neighbor_count": len(pages) - hit_count,
        "pages": pages,
        "graph_edges": graph_edges,
        "save_flag": hit_count >= 3,  # pre-signal for Claude's synthesis detection
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
