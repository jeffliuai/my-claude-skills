#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("Error: chromadb is not installed. Please try: pip install chromadb")
    exit(1)

from google import genai

# --- Configuration ---
VAULT_ROOT = Path("/Users/jeffliu/Documents/A05_Obsidian Vault")
WIKI_DIR = VAULT_ROOT / "300 LLM-Wiki"
INDEX_DIR = WIKI_DIR / ".ai_index"
DB_DIR = INDEX_DIR / "chroma_db"
GRAPH_DB = INDEX_DIR / "wiki_graph.db"
STATE_FILE = INDEX_DIR / "sync_state.json"

# Make sure index directory exists
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("Error: GEMINI_API_KEY not found in environment.")
    exit(1)

# Custom embedding function using new google-genai SDK + gemini-embedding-2
class GeminiGenAiEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, key: str, model: str = "models/gemini-embedding-2"):
        self.client = genai.Client(api_key=key)
        self.model_name = model

    def __call__(self, input: list) -> list:
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=input
        )
        return [e.values for e in response.embeddings]

    def name(self):
        return "GeminiGenAiEmbeddingFunction"

gemini_ef = GeminiGenAiEmbeddingFunction(key=api_key)

# Initialize ChromaDB Client
chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
collection = chroma_client.get_or_create_collection(
    name="llm_wiki_cards",
    embedding_function=gemini_ef,
    metadata={"hnsw:space": "cosine"}
)

# Initialize SQLite
def init_sqlite():
    conn = sqlite3.connect(str(GRAPH_DB))
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            subject TEXT,
            predicate TEXT,
            object TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    return conn

def extract_meta_with_ai(content):
    """
    Uses Gemini to extract a short summary and an array of relation graph tuples.
    Returns (summary_text, list_of_edges)
    """
    prompt = f"""你是精通知識萃取的助手。請閱讀以下文獻內容，並完成兩件事：
1. 提取出一段約 150-200 字以內的「核心摘要 (summary)」。
2. 從內容中萃取出最重要的 3-5 組實體關聯圖譜 (Entity-Relationship Graph)，這將幫助我們回答如"誰做了什麼事"或"什麼技術解決了什麼問題"。
表示為 subject, predicate, object (主詞, 關係, 受詞)。例如：
- {{"subject": "ITRI", "predicate": "develops", "object": "Open RAN"}}
- {{"subject": "Llama 3", "predicate": "is an alternative to", "object": "GPT-4"}}

請僅以 JSON 格式回覆，格式如下：
{{
  "summary": "這裡放核心摘要...",
  "graph": [
     {{"subject": "實體A", "predicate": "關係", "object": "實體B"}}
  ]
}}

文獻內容：
{content[:8000]}  # 截斷以防超過 Token (一般足夠做摘要)
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=prompt,
        )
        res_text = response.text.strip()
        import re
        res_text = re.sub(r'^```json\s*|\s*```$', '', res_text, flags=re.MULTILINE)
        data = json.loads(res_text)
        return data.get("summary", "無法生成摘要"), data.get("graph", [])
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "摘要生成失敗", []

def run_ingest():
    conn = init_sqlite()
    cursor = conn.cursor()
    
    # Load sync state
    sync_state = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                sync_state = json.load(f)
        except json.JSONDecodeError:
            pass
            
    all_md_files = list(WIKI_DIR.rglob("*.md"))
    to_process = []
    
    for file_path in all_md_files:
        # Skip files inside .ai_index or other hidden dirs if they exist
        if ".ai_index" in file_path.parts:
            continue
            
        mtime = os.path.getmtime(file_path)
        rel_str = str(file_path.relative_to(WIKI_DIR))
        
        last_mtime = sync_state.get(rel_str, 0)
        if mtime > last_mtime:
            to_process.append((file_path, rel_str, mtime))
            
    if not to_process:
        print("✅ 全量同步檢查完成：0 files need updating.")
        return
        
    print(f"🚀 開始 Ingest 任務：找到 {len(to_process)} 個檔案需要更新/建立索引...")
    
    success_count = 0
    for idx, (file_path, rel_str, mtime) in enumerate(to_process, 1):
        filename = file_path.name
        print(f"[{idx}/{len(to_process)}] 正在處理: {filename}")
        
        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                continue
                
            summary, graph_edges = extract_meta_with_ai(content)
            
            # --- 1. Update ChromaDB ---
            # We use the document's relative path as its unique ID in ChromaDB.
            # We index the summary, not the raw content, to optimize embedding search.
            collection.upsert(
                documents=[summary],
                metadatas=[{"filename": filename, "path": rel_str}],
                ids=[rel_str]
            )
            
            # --- 2. Update SQLite Graph ---
            # First delete old edges mapping to this file to prevent duplicates on update
            cursor.execute("DELETE FROM graph_edges WHERE source_file=?", (rel_str,))
            
            timestamp_now = datetime.datetime.now().isoformat()
            for edge in graph_edges:
                sub = edge.get("subject", "")
                pred = edge.get("predicate", "")
                obj = edge.get("object", "")
                if sub and pred and obj:
                    cursor.execute('''
                        INSERT INTO graph_edges (source_file, subject, predicate, object, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (rel_str, sub, pred, obj, timestamp_now))
            
            conn.commit()
            
            # Update sync state in memory
            sync_state[rel_str] = mtime
            success_count += 1
            
            # Rate limit protection (Gemini free tier or general safety)
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ 處理 {filename} 時發生錯誤: {e}")
            
    # Save the updated sync state
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sync_state, f, ensure_ascii=False, indent=2)
        
    print(f"🎉 Ingest 任務完成！成功更新 {success_count} 個檔案索引與關聯圖譜。")
    conn.close()

if __name__ == "__main__":
    if not WIKI_DIR.exists():
        print(f"找不到目標目錄: {WIKI_DIR}")
        exit(1)
    run_ingest()
