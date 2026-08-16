"""Batch re-index all LLM-Wiki markdown files into ChromaDB."""
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load GEMINI_API_KEY from .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

WIKI_DIR = Path("/Users/jeffliu/Documents/A05_Obsidian Vault/300 LLM-Wiki")
SKIP_FILES = {"000_index.md", "001_log.md"}

sys.path.insert(0, str(Path(__file__).parent))
from ingest_unified import index_file

files = sorted([
    f for f in WIKI_DIR.glob("*.md")
    if f.name not in SKIP_FILES and not f.name.startswith(".")
])

print(f"📚 Found {len(files)} files to index\n")

ok, fail = 0, []
for i, f in enumerate(files, 1):
    try:
        index_file(f)
        ok += 1
        if i % 10 == 0:
            print(f"  [{i}/{len(files)}] ...")
        time.sleep(0.3)  # gentle rate limit
    except Exception as e:
        fail.append((f.name, str(e)))
        print(f"  ❌ {f.name}: {e}")

print(f"\n✅ Done: {ok} indexed, {len(fail)} failed")
if fail:
    for name, err in fail:
        print(f"  ❌ {name}: {err}")
