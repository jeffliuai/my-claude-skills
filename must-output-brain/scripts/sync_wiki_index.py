#!/usr/bin/env python3
"""
sync_wiki_index.py — Reconcile 300 LLM-Wiki/ files against the ChromaDB/SQLite/sync_state index.

Detection is done by lint_wiki.py's check_index_consistency() (dependency-free,
via sync_state.json). This script performs the fix, once Jeff has confirmed via /lint:

Usage:
  python3 sync_wiki_index.py --fix-missing   # index real files that were never indexed
  python3 sync_wiki_index.py --fix-ghosts    # remove index entries whose file no longer exists
  python3 sync_wiki_index.py --fix-missing --fix-ghosts   # both
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ingest_unified import WIKI_DIR, DB_DIR, GRAPH_DB, STATE_FILE, index_file  # noqa: E402


def load_sync_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_real_files() -> set:
    real = {f.name for f in WIKI_DIR.glob("*.md")}
    return real


def fix_missing():
    real = get_real_files()
    sync_state = load_sync_state()
    missing = sorted(real - set(sync_state.keys()))
    if not missing:
        print("✅ No missing-index files.")
        return
    print(f"Indexing {len(missing)} missing files...")
    failed = []
    for name in missing:
        try:
            index_file(WIKI_DIR / name)
        except Exception as e:
            print(f"⚠️  Failed to index {name}: {e}")
            failed.append(name)
    print(f"Done: {len(missing) - len(failed)} indexed, {len(failed)} failed.")


def fix_ghosts():
    real = get_real_files()
    sync_state = load_sync_state()
    ghosts = sorted(set(sync_state.keys()) - real)
    if not ghosts:
        print("✅ No ghost index entries.")
        return
    print(f"Removing {len(ghosts)} ghost entries: {ghosts}")

    try:
        import chromadb
        chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
        collection = chroma_client.get_collection(name="llm_wiki_cards")
        collection.delete(ids=ghosts)
        print("  ChromaDB: removed.")
    except ImportError:
        print("  ⚠️  chromadb not installed, skipping vector cleanup.")
    except Exception as e:
        print(f"  ⚠️  ChromaDB ghost cleanup failed (may already be gone): {e}")

    conn = sqlite3.connect(str(GRAPH_DB))
    cursor = conn.cursor()
    for g in ghosts:
        cursor.execute("DELETE FROM graph_edges WHERE source_file=?", (g,))
    conn.commit()
    conn.close()
    print("  SQLite graph_edges: cleaned.")

    for g in ghosts:
        sync_state.pop(g, None)
    STATE_FILE.write_text(json.dumps(sync_state, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  sync_state.json: cleaned.")

    print(f"Done: {len(ghosts)} ghost entries removed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix-missing", action="store_true")
    parser.add_argument("--fix-ghosts", action="store_true")
    args = parser.parse_args()

    if not args.fix_missing and not args.fix_ghosts:
        parser.error("Specify --fix-missing and/or --fix-ghosts")

    if args.fix_missing:
        fix_missing()
    if args.fix_ghosts:
        fix_ghosts()
