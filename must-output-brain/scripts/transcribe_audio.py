#!/usr/bin/env python3
import sys
import os
import whisper
import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).parent.parent / ".env")

# Adjust paths relative to the script location if needed
OBSIDIAN_INBOX = Path("/Users/jeffliu/Documents/A05_Obsidian Vault/003 CALENDAR")

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
    print("Warning: GEMINI_API_KEY not found in environment. AI polishing will be skipped.")

def polish_text(text):
    if not client:
        return text
    
    print("Polishing text with Gemini...")
    
    prompt = f"""你是一個專業的文字編輯。以下是一段由語音轉文字產生的原始稿件。
請幫我進行以下處理：
1. 修正同音異義字錯誤（例如：抗試 -> 扛事, 有性 -> 隱性）。
2. 根據語意加上正確的標點符號。
3. 保持語氣自然，不要過度潤飾，只需修正明顯的錯誤。
4. 輸出格式請直接提供修正後的正體中文內容。

原始稿件：
{text}
"""
    
    response = client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=prompt
    )
    return response.text.strip()

def transcribe(audio_path, model_size="turbo"):
    if not os.path.exists(audio_path):
        print(f"Error: File {audio_path} not found.")
        return

    print(f"Loading Whisper model '{model_size}'...")
    model = whisper.load_model(model_size)

    print(f"Transcribing {audio_path}...")
    
    # Initial prompt for Whisper to guide punctuation and terminology
    initial_prompt = "以下是一段關於職場、領導力與個人成長的談話。內容包含：精兵良將、賦能、授權、隱性缺失、管理預期、非對稱優勢、溝通、執行力。請使用正體中文並加上正確的標點符號。"
    
    result = model.transcribe(
        audio_path, 
        verbose=False, 
        language='zh',
        initial_prompt=initial_prompt
    )

    raw_text = result["text"]
    
    # Polishing step with Gemini
    polished_text = polish_text(raw_text)
    
    # Save to Obsidian
    audio_file = Path(audio_path)
    base_name = audio_file.stem.replace("fb_video_", "")
    output_filename = f"Transcript_{base_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.md"
    output_path = OBSIDIAN_INBOX / output_filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcript for {audio_file.name}\n\n")
        f.write(f"**Date**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source**: {audio_path}\n\n")
        f.write("## Polished Content (Gemini)\n\n")
        f.write(polished_text)
        f.write("\n\n---\n## Raw Content (Whisper)\n\n")
        f.write(raw_text)
        f.write("\n\n---\n#Notes #Transcription #GeminiPolished")

    print(f"Transcription and polishing complete! Saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 transcribe_audio.py <audio_file_path>")
        sys.exit(1)
    
    transcribe(sys.argv[1])
