#!/usr/bin/env python3
import sys
import json
import os
import fcntl
import datetime
import re
from pathlib import Path

# Add current dir to path
sys.path.append(str(Path(__file__).parent))
import vault_utils

def process_messages():
    """
    Main sync logic:
    1. Read .tg_pending.json
    2. Categorize by Rule 1 (Ideas) or Rule 2 (Daily Sync)
    3. Execute sync
    4. Save state
    """
    PENDING_FILE = vault_utils.INBOX_DIR / ".tg_pending.json"

    if not PENDING_FILE.exists():
        print("No pending file found.")
        return 0, 0, 0

    # Exclusive lock across processes (shared with tg_listener.py) to prevent
    # concurrent read-modify-write cycles from silently clobbering each other.
    with open(PENDING_FILE, "r+", encoding="utf-8") as pf:
        fcntl.flock(pf, fcntl.LOCK_EX)
        try:
            return _process_locked(pf)
        finally:
            fcntl.flock(pf, fcntl.LOCK_UN)


def _process_locked(pf):
    pf.seek(0)
    raw = pf.read()
    try:
        data = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError:
        print("Error reading pending file.")
        return 0, 0, 0

    count_rule_1 = 0
    count_rule_2 = 0
    count_rule_url = 0
    
    # URL Regex Pattern
    url_pattern = re.compile(r'https?://[^\s]+')
    
    for entry in data:
        if entry.get("processed"):
            continue
            
        text = entry.get("text", "").strip()
        timestamp = entry.get("timestamp")
        
        if not text:
            entry["processed"] = True
            continue

        # URL Detection (Rule 3)
        urls = url_pattern.findall(text)
        
        try:
            # Rule 1: Starts with "我有一個想法"
            if text.startswith("我有一個想法"):
                print(f"Rule 1 matched (Idea): {text[:30]}...")
                # Use Gemini to extract title and refine content
                title, refined, tags = vault_utils.refine_idea_with_ai(text)
                curr_id = vault_utils.get_now_id()
                connections = vault_utils.find_connections(refined)
                vault_utils.create_note(curr_id, title, text, refined, tags, connections)
                entry["processed"] = True
                count_rule_1 += 1

            # Rule 3: Single URL or mostly URL
            elif len(urls) > 0 and len(text) < 500: # Heuristic to separate pure URLs from long essays with a URL
                target_url = urls[0] # Just grab the first one
                print(f"Rule 3 matched (URL): {target_url}")

                # 1. Create Temporary Card in Inbox
                dt_now = datetime.datetime.fromisoformat(timestamp) if timestamp else datetime.datetime.now()
                inbox_filename = vault_utils.create_inbox_note(text, dt_now)

                # 2. Append to Activity Log with Link
                inbox_link = f"000 INBOX/{inbox_filename}"
                vault_utils.append_to_activity_log(text, timestamp, inbox_link)

                entry["processed"] = True
                count_rule_url += 1

            # Rule 2: General note -> Temporary Card in Inbox + Log in Daily Note
            else:
                print(f"Rule 2 matched: {text[:30]}...")

                # 1. Create Temporary Card in Inbox
                dt_now = datetime.datetime.fromisoformat(timestamp) if timestamp else datetime.datetime.now()
                inbox_filename = vault_utils.create_inbox_note(text, dt_now)

                # 2. Append to Activity Log with Link
                inbox_link = f"000 INBOX/{inbox_filename}"
                vault_utils.append_to_activity_log(text, timestamp, inbox_link)

                entry["processed"] = True
                count_rule_2 += 1

        except Exception as e:
            print(f"[ERROR] Failed to process message (ts={timestamp}): {e}")

    # Write back within the same locked file handle
    pf.seek(0)
    pf.truncate()
    json.dump(data, pf, ensure_ascii=False, indent=2)
    pf.flush()
    os.fsync(pf.fileno())

    return count_rule_1, count_rule_2, count_rule_url

if __name__ == "__main__":
    r1, r2, r_url = process_messages()
    print(f"Sync Result: Rule 1 ({r1} ideas), Rule 2 ({r2} logs), Rule 3 ({r_url} URLs)")
