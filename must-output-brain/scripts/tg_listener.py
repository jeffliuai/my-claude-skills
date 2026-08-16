#!/usr/bin/env python3
import telebot
import os
import json
import fcntl
import datetime
from pathlib import Path

# Configuration
TOKEN_FILE = Path(__file__).parent / "tg_token.txt"
PENDING_FILE = Path("/Users/jeffliu/Documents/A05_Obsidian Vault/000 INBOX/.tg_pending.json")

def get_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None

def save_to_pending(text):
    if not PENDING_FILE.exists():
        PENDING_FILE.write_text("[]", encoding="utf-8")

    # Exclusive lock across processes (shared with robust_sync_tg.py) to prevent
    # concurrent read-modify-write cycles from silently clobbering each other.
    with open(PENDING_FILE, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            raw = f.read()
            try:
                data = json.loads(raw) if raw.strip() else []
            except json.JSONDecodeError as e:
                print(f"Error reading pending file, refusing to overwrite existing data: {e}")
                return

            data.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "text": text,
                "processed": False
            })

            try:
                f.seek(0)
                f.truncate()
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            except Exception as e:
                print(f"Failed to save message: {e}")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

token = get_token()
if not token:
    print("Error: No bot token found in tg_token.txt")
    print("Please create the file /Users/jeffliu/my-claude-skills/must-output-brain/scripts/tg_token.txt and paste your Telegram Bot Token in it.")
    exit(1)

bot = telebot.TeleBot(token)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """處理圖片訊息"""
    try:
        # 獲取最高解析度的圖片
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 生成檔名
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        image_filename = f"{timestamp}_tg_image.jpg"
        image_path = Path("/Users/jeffliu/Documents/A05_Obsidian Vault/000 INBOX") / image_filename
        
        # 保存圖片
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
        
        # 獲取圖片說明（caption）
        caption = message.caption if message.caption else "（無說明）"
        
        # 組合文字：說明 + 圖片名稱 (使用 Obsidian 內置連結格式)
        text_with_image = f"{caption}\n\n![[{image_filename}]]"
        
        print(f"Received image with caption: {caption}")
        save_to_pending(text_with_image)
        bot.reply_to(message, f"✅ 圖片已儲存至 Obsidian Inbox：{image_filename}")
        
    except Exception as e:
        print(f"Error handling photo: {e}")
        bot.reply_to(message, f"❌ 圖片處理失敗：{e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """處理文件訊息"""
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 生成檔名
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        original_name = message.document.file_name
        doc_filename = f"{timestamp}_{original_name}"
        doc_path = Path("/Users/jeffliu/Documents/A05_Obsidian Vault/000 INBOX") / doc_filename
        
        # 保存文件
        with open(doc_path, 'wb') as f:
            f.write(downloaded_file)
        
        # 獲取文件說明（caption）
        caption = message.caption if message.caption else f"上傳文件：{original_name}"
        
        # 如果是文字類文件，嘗試讀取內容
        content_preview = ""
        if original_name.endswith(('.txt', '.md', '.py', '.json')):
            try:
                content_preview = downloaded_file.decode('utf-8')
                # 如果內容太大，只取一部分做 metadata，但全文已存在檔案中
                text_to_save = content_preview
            except:
                text_to_save = f"{caption}\n\n檔案路徑：[[{doc_filename}]]"
        else:
            text_to_save = f"{caption}\n\n檔案路徑：[[{doc_filename}]]"
            
        print(f"Received document: {original_name}")
        save_to_pending(text_to_save)
        bot.reply_to(message, f"✅ 文件已儲存至 Obsidian Inbox：{doc_filename}")
        
    except Exception as e:
        print(f"Error handling document: {e}")
        bot.reply_to(message, f"❌ 文件處理失敗：{e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """處理文字訊息"""
    text = message.text if message.text else ""
    print(f"Received message length: {len(text)}")
    # Log raw for debugging large messages
    with open("/tmp/tg_raw_last_message.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    save_to_pending(text)
    bot.reply_to(message, f"✅ 想法已記錄 (長度: {len(text)})，等待同步。")

print(f"[{datetime.datetime.now().isoformat()}] Telegram Listener Started (v2.2)... Press Ctrl+C to stop.")
while True:
    try:
        # Reduced timeouts to stay under standard proxy/firewall idle limits (30-60s)
        # Shorter timeouts help maintain a 'warm' session and detect disconnects faster.
        bot.infinity_polling(timeout=20, long_polling_timeout=20, logger_level=None)
    except Exception as e:
        # Adding a delay prevents the 'Death Loop' where launchd restarts the process too fast
        # which can trigger 409 Conflicts at the Telegram API level.
        print(f"[{datetime.datetime.now().isoformat()}] Polling critical failure: {e}")
        import time
        print("Waiting 10 seconds before robust retry...")
        time.sleep(10)
