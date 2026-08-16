#!/usr/bin/env python3
import os
import re
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).parent.parent / ".env")

# 簡繁轉換工具
try:
    from opencc import OpenCC
    s2t_converter = OpenCC('s2t')  # Simplified to Traditional
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False
    print("Warning: opencc-python-reimplemented not installed. Simplified Chinese will not be converted.")

VAULT_ROOT = Path("/Users/jeffliu/Documents/A05_Obsidian Vault")
INBOX_DIR = VAULT_ROOT / "000 INBOX"
CARDS_DIR = VAULT_ROOT / "002 CARDS"
CALENDAR_DIR = VAULT_ROOT / "003 CALENDAR"

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
    print("Warning: GEMINI_API_KEY not found in environment. AI summarization will be skipped.")

def get_now_id():
    # Use seconds for higher precision to avoid collisions if processed rapidly
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def get_now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def sanitize_filename(filename):
    # Remove illegal characters and replace all whitespace (newlines, tabs, etc.) with space
    # Also remove brackets [] which interfere with Markdown links
    name = re.sub(r'[\\/*?:"<>|\n\r\t\[\]!]', " ", filename).strip()
    return re.sub(r'\s+', " ", name) # Collapse multiple spaces

def find_connections(content, limit=5):
    """
    Very simple keyword-based connection finder.
    """
    # Extract keywords (simple regex for Chinese/English words longer than 2 chars)
    keywords = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', content)
    
    # Filter out common/utility keywords that lead to junk connections
    blacklist_keywords = {"Telegram", "capture", "快速同步", "說明", "圖片"}
    unique_keywords = [k for k in list(dict.fromkeys(keywords)) if k not in blacklist_keywords][:10]
    
    connections = []
    # Scan filenames in CARDS and SOURCE for keyword matches
    search_dirs = [CARDS_DIR, VAULT_ROOT / "100 REPORT", VAULT_ROOT / "201 SIDE PROJECT"]
    
    # Blacklist pattern for test files
    test_pattern = re.compile(r'測試|test', re.I)
    
    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for file in s_dir.glob("*.md"):
            # Skip test files
            if test_pattern.search(file.name):
                continue
                
            for kw in unique_keywords:
                if kw in file.name:
                    connections.append(file.stem)
                    break
            if len(connections) >= limit:
                break
        if len(connections) >= limit:
            break
            
    return list(set(connections))

def get_week_folder_name(dt=None):
    if dt is None:
        dt = datetime.datetime.now()
    # Find Monday of that week
    monday = dt - datetime.timedelta(days=dt.weekday())
    year = monday.year
    # ISO week number
    week_num = dt.isocalendar()[1]
    return f"{year}-W{week_num:02d}"

def find_daily_note(date_str):
    """Recursively find a daily note by name in the CALENDAR_DIR."""
    filename = f"{date_str} Daily Note.md"
    for path in CALENDAR_DIR.rglob(filename):
        return path
    return None

def update_daily_note(card_title, card_id):
    """
    Appends a link to the new card in the today's daily note under # Ideas.
    """
    if HAS_OPENCC:
        card_title = s2t_converter.convert(card_title)
        
    now = datetime.datetime.now()
    date_str = now.strftime("%Y_%m_%d")
    daily_note_path = find_daily_note(date_str)
    
    if not daily_note_path:
        # Create it in the week folder if not found
        week_folder = CALENDAR_DIR / get_week_folder_name(now)
        week_folder.mkdir(parents=True, exist_ok=True)
        daily_note_path = week_folder / f"{date_str} Daily Note.md"
        # Initialize with Standardized structure
        with open(daily_note_path, 'w', encoding='utf-8') as f:
            f.write(f"""---
creation date: {now.strftime("%Y-%m-%d %H:%M")}
modification date: {now.strftime("%Y-%m-%d %H:%M")}
---

# {date_str} Daily Note

# I. 每日活動 / 雜記

# II. 工作

*本日 AAR (After Action Review)*
### 1. 選一件讓我有感覺、有啟發的事情

### 2. 我從過程中學習到什麼事情 ?

### 3. 下次要如何做可以更好/有可以更好的地方嗎？

# Ideas
*把腦中靈感都放在這個區域*

""")
        print(f"Created new daily note: {daily_note_path}")

    card_link = f"- [[{card_id} {card_title}]]"
    
    with open(daily_note_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    found_ideas = False
    section_index = -1
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip().startswith("# Ideas"):
            found_ideas = True
            section_index = i
            
    if found_ideas:
        # Insert at the top of the section, right after the description line if it exists
        insert_at = section_index + 1
        if insert_at < len(new_lines) and "*把腦中靈感都放在這個區域*" in new_lines[insert_at]:
            insert_at += 1
        
        # Ensure previous line ends with a newline
        if insert_at > 0 and not new_lines[insert_at-1].endswith('\n'):
            new_lines[insert_at-1] += '\n'
            
        new_lines.insert(insert_at, f"{card_link}\n")
    else:
        # If # Ideas doesn't exist, append to end
        if not lines or not lines[-1].strip() == "":
            new_lines.append("\n")
        new_lines.append(f"# Ideas\n*把腦中靈感都放在這個區域*\n{card_link}\n")

    with open(daily_note_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return daily_note_path.stem

def summarize_text(text, target_words=100):
    """
    Generates an AI summary of the text using Gemini.
    """
    if not client:
        return text[:target_words*2] + "..." # Fallback to truncation
    
    prompt = f"""請幫我根據以下文字產生一段約 {target_words} 字的摘要。
這是一段從 Telegram 截取的「臨時卡片/摘錄」，請提取核心內容，不需要任何前言或引號。
使用正體中文。

文字內容：
{text}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Summarization error: {e}")
        return text[:target_words*2] + "..."

def refine_idea_with_ai(text):
    """
    Uses Gemini to transform a raw idea into a formal card structure.
    Returns (title, refined_content, tags)
    """
    if not client:
        return "新想法", text, "#筆記/靈感"
        
    prompt = f"""你是我的知識管理助手。請幫我將這段關於『我有一個想法』的 Telegram 訊息轉化為正式的 Zettelkasten 筆記。
1. 提取一個簡短有力的標題 (Title)。
2. 將原始內容整理成更有條理、更深刻的段落 (Refined Content)。
3. 建議 2-3 個標籤 (Tags)，以 # 開頭。

請僅以 JSON 格式回覆，格式如下：
{{
  "title": "標題",
  "refined_content": "整理後的內容",
  "tags": "#標籤1 #標籤2"
}}

文字內容：
{text}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=prompt
        )
        # Parse JSON from response
        res_text = response.text.strip()
        # Remove markdown code blocks if present
        res_text = re.sub(r'^```json\s*|\s*```$', '', res_text, flags=re.MULTILINE)
        data = json.loads(res_text)
        return data.get("title", "新想法"), data.get("refined_content", text), data.get("tags", "#筆記/靈感")
    except Exception as e:
        print(f"AI Refinement error: {e}")
        return "新想法", text, "#筆記/靈感"

def refine_url_with_ai(url, title, content):
    """
    Uses Gemini to transform a crawled web page into a formal card structure.
    Returns (title, refined_content, tags)
    """
    if not client:
        return title, content, "#網路文章"
        
    prompt = f"""你是我的知識管理助手。請幫我將這篇網頁文章轉化為正式的 Zettelkasten 筆記。
1. 提取一個有意義且簡短有力的標題 (Title)，可以基於原網頁標題或內容重新命名。
2. 寫出一份結構化的摘要與核心觀點 (Refined Content)。內容必須包含「摘要 (Summary)」與「核心觀點 (Key Takeaways)」兩個小節，其中核心觀點應以條列式列出。
3. 建議 2-4 個標籤 (Tags)，以 # 開頭，其中必須包含 #網路文章。

請僅以 JSON 格式回覆，格式如下：
{{
  "title": "標題",
  "refined_content": "整理後的內容",
  "tags": "#標籤1 #標籤2"
}}

網址：{url}
原始標題：{title}
內文擷取：
{content[:4000]}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=prompt
        )
        res_text = response.text.strip()
        res_text = re.sub(r'^```json\s*|\s*```$', '', res_text, flags=re.MULTILINE)
        data = json.loads(res_text)
        
        # Append URL source to content
        refined = data.get("refined_content", content)
        
        return data.get("title", title), refined, data.get("tags", "#網路文章")
    except Exception as e:
        print(f"AI URL Refinement error: {e}")
        return title, content, "#網路文章"

def create_inbox_note(text, timestamp=None):
    """
    Saves the full text as a .md file in the Inbox and returns the filename.
    """
    if HAS_OPENCC:
        text = s2t_converter.convert(text)
        
    now = timestamp if timestamp else datetime.datetime.now()
    note_id = now.strftime("%Y%m%d%H%M%S")
    
    # Extract first line or a few words for the title
    first_line = text.split('\n')[0][:30]
    title = sanitize_filename(first_line)
    filename = f"{note_id} TG_Excerpt_{title}.md"
    file_path = INBOX_DIR / filename
    
    content = f"""---
source: Telegram
date: {now.strftime("%Y-%m-%d %H:%M:%S")}
type: Temporary Card
---
# TG 摘錄：{title}

{text}

---
#TG/摘錄 #Inbox
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename

def append_to_activity_log(text, timestamp_str=None, inbox_link=None):
    """
    Appends a TG message to the activity log (# I. 每日活動 / 雜記) in today's daily note.
    If inbox_link is provided, it links to the raw note in Inbox.
    """
    if HAS_OPENCC:
        text = s2t_converter.convert(text)

    # Always write to TODAY's Daily Note regardless of when the message was sent.
    # Using message timestamp caused messages sent before midnight to silently land
    # in the previous day's note, making them appear "missing" to the user.
    now = datetime.datetime.now()

    # Preserve the original send time for display in the log entry
    time_str = now.strftime("%H:%M")
    if timestamp_str:
        try:
            sent_at = datetime.datetime.fromisoformat(timestamp_str)
            time_str = sent_at.strftime("%H:%M")
        except ValueError:
            pass

    # Always use the raw text for the activity log as per user preference
    log_text = text

    date_str = now.strftime("%Y_%m_%d")
    
    daily_note_path = find_daily_note(date_str)
    if not daily_note_path:
        # Re-use update_daily_note logic to create if not exists
        update_daily_note("dummy", "dummy")
        daily_note_path = find_daily_note(date_str)

    with open(daily_note_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    found_section = False
    section_index = -1
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip().startswith("# I. 每日活動 / 雜記"):
            found_section = True
            section_index = i
            
    # Format A: 內容優先
    # - URL 訊息：直接顯示 URL，不附檔案連結
    # - 文字訊息：顯示前 40 字預覽，連結放後面
    url_pattern_local = re.compile(r'https?://[^\s]+')
    urls = url_pattern_local.findall(log_text)
    is_url_message = bool(urls) and len(log_text.strip()) < 300

    if is_url_message:
        log_entry = f"- [{time_str}] (TG) {urls[0]}\n"
    elif inbox_link:
        preview = log_text.replace('\n', ' ').strip()[:40]
        if len(log_text.strip()) > 40:
            preview += "..."
        log_entry = f"- [{time_str}] (TG) {preview} [[{inbox_link}]]\n"
    else:
        log_entry = f"- [{time_str}] (TG) {log_text}\n"
    
    if found_section:
        # Insert after the header
        insert_at = section_index + 1
        
        # Ensure previous line ends with a newline
        if insert_at > 0 and not new_lines[insert_at-1].endswith('\n'):
            new_lines[insert_at-1] += '\n'
            
        new_lines.insert(insert_at, log_entry)
    else:
        # If section doesn't exist, prepend it
        new_lines.insert(0, f"# I. 每日活動 / 雜記\n{log_entry}\n")

    with open(daily_note_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    return daily_note_path.name


def log_raw_to_daily(text):
    """
    Appends raw text to the today's daily note under # I. 每日活動 / 雜記.
    """
    if HAS_OPENCC:
        text = s2t_converter.convert(text)
        
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%Y_%m_%d")
    daily_note_path = find_daily_note(date_str)
    
    if not daily_note_path:
        # Create it in the week folder if not found
        week_folder = CALENDAR_DIR / get_week_folder_name(now)
        week_folder.mkdir(parents=True, exist_ok=True)
        daily_note_path = week_folder / f"{date_str} Daily Note.md"
        # Initialize
        with open(daily_note_path, 'w', encoding='utf-8') as f:
            f.write(f"# I. 每日活動 / 雜記\n\n# II. 工作\n\n*本日 AAR (After Action Review)*\n### 1. 選一件讓我有感覺、有啟發的事情\n\n### 2. 我從過程中學習到什麼事情 ?\n\n### 3. 下次要如何做可以更好/有可以更好的地方嗎？\n\n# Ideas\n*把腦中靈感都放在這個區域*\n\n")

    log_entry = f"[{time_str}] (TG) {text}"
    
    with open(daily_note_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    found_section = False
    section_index = -1
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip().startswith("# Ideas"):
            found_section = True
            section_index = i
            
    if found_section:
        # Find the end of the section (next header or end of file)
        insert_at = len(new_lines)
        for i in range(section_index + 1, len(new_lines)):
            if new_lines[i].strip().startswith("#"):
                # We reached a new section (like # II. 工作)
                insert_at = i
                break
        
        # Ensure blank line before next section if not already there
        if insert_at > 0 and not new_lines[insert_at-1].strip() == "":
            new_lines.insert(insert_at, "\n")
            insert_at += 1
            
        new_lines.insert(insert_at, f"{log_entry}\n")
    else:
        new_lines.insert(0, f"# I. 每日活動 / 雜記\n{log_entry}\n\n")

    with open(daily_note_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return daily_note_path.stem

def create_note(id, title, raw_content, refined_content, tags="#筆記/靈感", connections=None):
    """創建新筆記，自動轉換簡體中文為繁體中文"""
    
    # 自動轉換簡體為繁體
    if HAS_OPENCC:
        title = s2t_converter.convert(title)
        raw_content = s2t_converter.convert(raw_content)
        refined_content = s2t_converter.convert(refined_content)
        tags = s2t_converter.convert(tags)
        if connections:
            connections = [s2t_converter.convert(c) for c in connections]
    
    title = sanitize_filename(title)
    
    # Update today's daily note and get its name for backlinking
    daily_note_link = update_daily_note(title, id)
    
    # Ensure activity is logged in the Daily Note's activity log (Regression Fix)
    append_to_activity_log(raw_content)
    
    # 1. Save Raw to Inbox
    inbox_filename = f"{id} Raw.md"
    inbox_path = INBOX_DIR / inbox_filename
    
    # Prevent overwriting if ID somehow collides
    counter = 1
    while inbox_path.exists():
        inbox_filename = f"{id}_{counter} Raw.md"
        inbox_path = INBOX_DIR / inbox_filename
        counter += 1
    
    inbox_body = f"Original Input:\n\n{raw_content}\n\n---\nTarget Card: [[{id} {title}]]"
    
    with open(inbox_path, 'w', encoding='utf-8') as f:
        f.write(inbox_body)
        
    # 2. Save Refined to Cards
    card_filename = f"{id} {title}.md"
    card_path = CARDS_DIR / card_filename
    
    # Prevent overwriting
    counter = 1
    while card_path.exists():
        card_filename = f"{id}_{counter} {title}.md"
        card_path = CARDS_DIR / card_filename
        counter += 1
    
    # Ensure tags are properly formatted for YAML (either a list or a quoted string)
    # If tags are passed as "#tag1 #tag2", convert to a list or quoted string
    friendly_tags = tags
    if isinstance(tags, str) and tags.startswith("#"):
        # Convert "#tag1 #tag2" to "tag1, tag2" or similar
        # For Obsidian YAML, it's best to remove the '#' inside the tags field OR quote the whole thing
        # Let's just quote the whole string to be safe and preserve the user's '#' if they like them
        friendly_tags = f'"{tags}"'
    
    connections_str = ""
    if connections:
        connections_str = "\n".join([f"- [[{c}]]" for c in connections])
    
    card_content = f"""---
uid: {id}
created: {get_now_iso()}
tags: {friendly_tags}
---
# {title}

## 內容

{refined_content}

---
## 🔗 連結
- **歸檔 (Up):** [[000 INBOX/{inbox_filename}|原始輸入]]
- **日誌 (Daily):** [[{daily_note_link if daily_note_link else ''}]]
- **相關 (Related):**
{connections_str}
"""
    
    with open(card_path, 'w', encoding='utf-8') as f:
        f.write(card_content)
        
    return str(inbox_path), str(card_path)

def sync_telegram(process_func):
    """
    Reads .tg_pending.json and processes each unprocessed message using process_func.
    process_func should take the raw text and return (title, refined_content, tags)
    """
    PENDING_FILE = INBOX_DIR / ".tg_pending.json"
    count = 0
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return 0
    
    for entry in data:
        if not entry.get("processed"):
            print(f"Syncing: {entry['text']}")
            try:
                title, refined, tags = process_func(entry['text'])
                curr_id = get_now_id()
                connections = find_connections(refined)
                create_note(curr_id, title, entry['text'], refined, tags, connections)
                entry["processed"] = True
                count += 1
            except Exception as e:
                print(f"Error processing message: {e}")
                continue
            
    # Atomic-ish write: write to temp then rename
    temp_file = PENDING_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, PENDING_FILE)
        
    return count

if __name__ == "__main__":
    # Example usage for testing
    curr_id = get_now_id()
    # find_connections test
    # print(find_connections("長期主義 知識複利"))
