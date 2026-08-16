#!/usr/bin/env python3
"""
ingest_unified.py — Unified LLM-Wiki ingest pipeline

Subcommands:
  extract <source> [--self]   Extract content, output JSON for Claude (Claude Code mode)
  index   <file_path>         Index an existing MD file into ChromaDB + SQLite
  run     <source> [--self]   Full pipeline via Gemini (Antigravity mode)

Auto-detects LLM environment:
  CLAUDECODE env var present  → Claude Code (extract + index pattern)
  GEMINI_API_KEY only         → Gemini full pipeline
  --llm claude|gemini         → Force override
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import argparse
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# ── Optional deps ──────────────────────────────────────────────────────────────
try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    from pdfminer.high_level import extract_text as pdf_extract
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YOUTUBE = True
except ImportError:
    HAS_YOUTUBE = False

# ── Paths ──────────────────────────────────────────────────────────────────────
VAULT_ROOT  = Path("/Users/jeffliu/Documents/A05_Obsidian Vault")
WIKI_DIR    = VAULT_ROOT / "300 LLM-Wiki"
RAW_DIR     = VAULT_ROOT / "raw"
INDEX_DIR   = WIKI_DIR / ".ai_index"
DB_DIR      = INDEX_DIR / "chroma_db"
GRAPH_DB    = INDEX_DIR / "wiki_graph.db"
STATE_FILE  = INDEX_DIR / "sync_state.json"

# ── Mode A / B compilation rules ───────────────────────────────────────────────
RULES_A = """【編譯守則：模式 A — 外部知識吸收 (Origin: External)】
這是來自外部的知識。寫入 Wiki 時必須包含：
1. 核心摘要（150-200 字）
2. ⚠️ 認知衝突與張力 (Tension & Gaps)：這個新知識與 Jeff 既有概念有何矛盾或缺口？
3. 3-5 組知識圖譜（subject → predicate → object）
4. 建議標題（不含日期）與標籤

YAML 規範：檔名不加日期，YAML 加 created/updated。"""

RULES_B = """【編譯守則：模式 B — 自我成品反芻 (Origin: Self)】
這是 Jeff 自己的產出/對話/文章。寫入 Wiki 時：
1. 核心摘要（150-200 字）
2. 💡 Jeff 的實踐紀錄 (My Practice)：歸納核心結論、獨家解法或實戰數據
3. 尋找既有 Wiki 頁面作為宿主，追加段落而非新建頁面
4. 建立與原始成品的雙向連結
5. 3-5 組知識圖譜（subject → predicate → object）

YAML 規範：檔名不加日期，YAML 加 created/updated。"""

# ── Environment detection ──────────────────────────────────────────────────────
def detect_llm() -> str:
    if os.environ.get("CLAUDECODE"):
        return "claude"
    elif os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    raise EnvironmentError(
        "Cannot detect LLM environment.\n"
        "Run inside Claude Code, or set GEMINI_API_KEY."
    )

# ── Source extraction ──────────────────────────────────────────────────────────
def _is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url or "youtube.com/shorts/" in url


def _extract_youtube_id(url: str) -> str:
    import re
    for pattern in [
        r"youtube\.com/watch\?.*v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
    ]:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return ""


def _get_youtube_title(url: str) -> str:
    try:
        import re
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="ignore")
        m = re.search(r"<title>(.+?)</title>", html)
        if m:
            return m.group(1).replace(" - YouTube", "").strip()
    except Exception:
        pass
    return ""


def _extract_youtube(url: str) -> str:
    """Extract YouTube transcript; falls back to URL scrape if unavailable."""
    if not HAS_YOUTUBE:
        sys.exit(
            "youtube-transcript-api not installed.\n"
            "Run: pip install youtube-transcript-api"
        )

    video_id = _extract_youtube_id(url)
    if not video_id:
        sys.exit(f"Cannot parse YouTube video ID from: {url}")

    try:
        api = YouTubeTranscriptApi()

        # Try preferred languages directly via fetch()
        fetched = None
        for lang_combo in [
            ["zh-Hant", "zh-TW", "zh"],
            ["zh-Hant"],
            ["zh"],
            ["en"],
        ]:
            try:
                fetched = api.fetch(video_id, languages=lang_combo)
                break
            except Exception:
                continue

        # Last resort: fetch whatever is available
        if fetched is None:
            transcript_list = api.list(video_id)
            first = next(iter(transcript_list))
            fetched = first.fetch()

        text = " ".join(snippet.text for snippet in fetched)

        title = _get_youtube_title(url)
        header = f"[YouTube 逐字稿] {title}\nURL: {url}\n\n" if title else f"[YouTube 逐字稿]\nURL: {url}\n\n"
        return header + text

    except Exception as e:
        print(f"⚠️  YouTube transcript fetch failed ({e}), falling back to URL scrape.", file=sys.stderr)
        return _extract_url(url)


def extract_content(source: str) -> tuple:
    """Returns (content: str, source_type: str)"""
    source = source.strip()

    if source.startswith("http://") or source.startswith("https://"):
        if _is_youtube_url(source):
            return _extract_youtube(source), "YouTube"
        return _extract_url(source), "URL"

    path = Path(source)
    if path.exists():
        suffix = path.suffix.lower()
        if suffix in (".md", ".txt"):
            return path.read_text(encoding="utf-8"), f"file:{suffix}"
        elif suffix == ".pdf":
            if not HAS_PDF:
                sys.exit("pdfminer not installed. Run: pip install pdfminer.six")
            return pdf_extract(str(path)), "file:pdf"
        elif suffix in (".docx", ".doc"):
            if not HAS_DOCX:
                sys.exit("python-docx not installed. Run: pip install python-docx")
            doc = docx.Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs), "file:docx"
        else:
            # Try reading as plain text
            try:
                return path.read_text(encoding="utf-8"), f"file:{suffix}"
            except Exception as e:
                sys.exit(f"Cannot read file {source}: {e}")

    # Plain text input
    return source, "text"

def save_raw_content(source_url: str, content: str, source_type: str) -> str:
    """Save raw scraped content to raw/YYYY-MM/ folder. Returns relative path from VAULT_ROOT."""
    import re
    from urllib.parse import urlparse

    today = datetime.date.today()
    month_dir = RAW_DIR / today.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(source_url)
    path_part = parsed.path.rstrip("/")
    slug = path_part.split("/")[-1] if path_part and path_part != "/" else parsed.netloc
    slug = re.sub(r"[^\w\-]", "-", slug)[:50].strip("-")
    slug = slug or "article"

    filename = f"{today.strftime('%Y%m%d')}_{slug}.md"
    raw_path = month_dir / filename

    raw_path.write_text(
        f"---\nsource_url: \"{source_url}\"\nsource_type: \"{source_type}\"\nscraped: \"{today.isoformat()}\"\n---\n\n{content}",
        encoding="utf-8",
    )

    rel_path = str(raw_path.relative_to(VAULT_ROOT))
    print(f"💾 Raw saved: {rel_path}", file=sys.stderr)
    return rel_path


def _extract_url(url: str) -> str:
    """Fetch URL content as plain text."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
        # Strip HTML tags (basic)
        import re
        text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:12000]  # Cap to avoid token overflow
    except Exception as e:
        sys.exit(f"URL fetch failed: {e}")

# ── ChromaDB + SQLite indexing ─────────────────────────────────────────────────
def index_file(file_path: Path):
    """Index a single MD file.

    ChromaDB vector indexing is best-effort. SQLite graph indexing and
    sync_state updates must still run even when optional vector dependencies
    or embedding credentials are unavailable.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    file_path = file_path.expanduser()
    if not file_path.is_absolute():
        file_path = (VAULT_ROOT / file_path).resolve()
    else:
        file_path = file_path.resolve()

    content = file_path.read_text(encoding="utf-8")
    if not content.strip():
        print(f"⚠️  Empty file: {file_path.name}")
        return

    # Extract summary and graph from frontmatter/content for embedding
    # Use first 500 chars as embedding doc if no summary section found
    import re
    summary_match = re.search(r"## 核心摘要.*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    embed_text = summary_match.group(1).strip()[:1000] if summary_match else content[:500]

    rel_str = str(file_path.relative_to(WIKI_DIR))

    vector_indexed = False
    if not HAS_CHROMA:
        print("⚠️  chromadb not installed, skipping vector index.")
    elif not os.environ.get("GEMINI_API_KEY"):
        print("⚠️  GEMINI_API_KEY not set, skipping vector index.")
    else:
        try:
            from google import genai as google_genai

            class GeminiGenAiEmbeddingFunction(embedding_functions.EmbeddingFunction):
                def __init__(self, key: str, model: str = "models/gemini-embedding-2"):
                    self.client = google_genai.Client(api_key=key)
                    self.model_name = model

                def __call__(self, input: list) -> list:
                    response = self.client.models.embed_content(
                        model=self.model_name,
                        contents=input
                    )
                    return [e.values for e in response.embeddings]

                def name(self):
                    return "GeminiGenAiEmbeddingFunction"

            gemini_ef = GeminiGenAiEmbeddingFunction(key=os.environ["GEMINI_API_KEY"])
            chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
            collection = chroma_client.get_or_create_collection(
                name="llm_wiki_cards",
                embedding_function=gemini_ef,
                metadata={"hnsw:space": "cosine"},
            )
            collection.upsert(
                documents=[embed_text],
                metadatas=[{"filename": file_path.name, "path": rel_str}],
                ids=[rel_str],
            )
            vector_indexed = True
        except ImportError:
            print("⚠️  google-genai not installed, skipping vector index. Run: pip install google-genai")
        except Exception as e:
            print(f"⚠️  Vector index failed, continuing SQLite graph index: {e}")

    # SQLite: extract graph edges from content
    conn = sqlite3.connect(str(GRAPH_DB))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT, subject TEXT, predicate TEXT, object TEXT, created_at TEXT
        )
    """)
    cursor.execute("DELETE FROM graph_edges WHERE source_file=?", (rel_str,))

    # Parse knowledge graph lines: "subject → predicate → object"
    ts = datetime.datetime.now().isoformat()
    for line in content.splitlines():
        parts = [p.strip() for p in line.split("→")]
        if len(parts) == 3 and all(parts):
            cursor.execute(
                "INSERT INTO graph_edges (source_file, subject, predicate, object, created_at) VALUES (?,?,?,?,?)",
                (rel_str, parts[0].lstrip("-• "), parts[1], parts[2], ts),
            )

    conn.commit()
    conn.close()

    # Update sync state
    sync_state = {}
    if STATE_FILE.exists():
        try:
            sync_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    sync_state[rel_str] = os.path.getmtime(file_path)
    STATE_FILE.write_text(json.dumps(sync_state, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Indexed: {file_path.name}")

# ── Gemini full pipeline ───────────────────────────────────────────────────────
def run_with_gemini(source: str, is_self: bool):
    """Full pipeline: extract → Gemini refine → write MD → index."""
    try:
        from google import genai as google_genai
    except ImportError:
        sys.exit("google-genai not installed. Run: pip install google-generativeai")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY not set.")

    client = google_genai.Client(api_key=api_key)
    content, source_type = extract_content(source)
    rules = RULES_B if is_self else RULES_A

    raw_path = None
    if source_type in ("URL", "YouTube") and not is_self:
        raw_path = save_raw_content(source.strip(), content, source_type)

    prompt = f"""你是 Jeff Liu 的知識管理助手。請根據以下規則處理輸入內容，以 JSON 格式回覆。

{rules}

輸入來源類型：{source_type}
輸入內容：
{content[:8000]}

請回覆 JSON 格式：
{{
  "title": "建議標題（不含日期）",
  "summary": "核心摘要（150-200字）",
  "tags": ["標籤1", "標籤2"],
  "graph": [
    {{"subject": "實體A", "predicate": "關係", "object": "實體B"}}
  ],
  "body": "完整 Wiki 頁面內容（Markdown，含 YAML frontmatter）"
}}"""

    response = client.models.generate_content(
        model="gemini-2.0-flash-001", contents=prompt
    )
    res_text = response.text.strip()
    import re
    res_text = re.sub(r"^```json\s*|\s*```$", "", res_text, flags=re.MULTILINE)

    try:
        data = json.loads(res_text)
    except json.JSONDecodeError as e:
        sys.exit(f"Gemini returned invalid JSON: {e}\n{res_text[:300]}")

    title = data.get("title", "Untitled")
    body  = data.get("body", "")

    # Inject source metadata into YAML frontmatter
    if raw_path or source_type in ("URL", "YouTube"):
        import re as _re
        source_meta = ""
        if source_type in ("URL", "YouTube"):
            source_meta += f'\nsource_url: "{source.strip()}"'
        if raw_path:
            source_meta += f'\nsource_raw_path: "{raw_path}"'
        body = _re.sub(r"^(---\n)", r"\1" + source_meta.lstrip("\n") + "\n", body, count=1)

    # Write to LLM-Wiki
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    safe_title = re.sub(r'[\\/*?:"<>|]', " ", title).strip()
    file_path = WIKI_DIR / f"{safe_title}.md"
    file_path.write_text(body, encoding="utf-8")
    print(f"📄 Created: {file_path.name}")

    # Index
    index_file(file_path)
    print(f"\n🎉 Done. Card: [[{safe_title}]]")
    print("💡 Reminder: run Lint to check for orphan pages.")

# ── Claude Code extract mode ───────────────────────────────────────────────────
def run_extract(source: str, is_self: bool):
    """Extract content and print JSON payload for Claude to process."""
    content, source_type = extract_content(source)
    rules = RULES_B if is_self else RULES_A

    raw_path = None
    if source_type in ("URL", "YouTube") and not is_self:
        raw_path = save_raw_content(source.strip(), content, source_type)

    output = {
        "mode": "extract",
        "source_type": source_type,
        "is_self": is_self,
        "compilation_rules": rules,
        "content_length": len(content),
        "content": content[:10000],
    }
    if raw_path:
        output["source_url"] = source.strip()
        output["raw_path"] = raw_path

    print(json.dumps(output, ensure_ascii=False, indent=2))

# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Unified LLM-Wiki ingest pipeline")
    sub = parser.add_subparsers(dest="cmd")

    # extract subcommand
    p_extract = sub.add_parser("extract", help="Extract content for Claude (Claude Code mode)")
    p_extract.add_argument("source")
    p_extract.add_argument("--self", action="store_true", dest="is_self")

    # index subcommand
    p_index = sub.add_parser("index", help="Index an existing MD file")
    p_index.add_argument("file_path")

    # run subcommand
    p_run = sub.add_parser("run", help="Full pipeline via Gemini (Antigravity mode)")
    p_run.add_argument("source")
    p_run.add_argument("--self", action="store_true", dest="is_self")
    p_run.add_argument("--llm", choices=["claude", "gemini"], default=None)

    args = parser.parse_args()

    if args.cmd == "extract":
        run_extract(args.source, args.is_self)

    elif args.cmd == "index":
        index_file(Path(args.file_path))

    elif args.cmd == "run":
        llm = args.llm or detect_llm()
        if llm == "gemini":
            run_with_gemini(args.source, args.is_self)
        else:
            # In Claude Code, 'run' falls back to extract for Claude to handle
            run_extract(args.source, args.is_self)

    else:
        # No subcommand: auto-detect and run
        if len(sys.argv) < 2:
            parser.print_help()
            sys.exit(1)
        # Treat first arg as source for backward compatibility
        llm = detect_llm()
        is_self = "--self" in sys.argv
        source_args = [a for a in sys.argv[1:] if a != "--self"]
        source = " ".join(source_args)
        if llm == "gemini":
            run_with_gemini(source, is_self)
        else:
            run_extract(source, is_self)

if __name__ == "__main__":
    main()
