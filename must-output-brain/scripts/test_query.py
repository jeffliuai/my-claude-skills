#!/usr/bin/env python3
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("Error: chromadb is not installed.")
    exit(1)

from google import genai

# --- Configuration ---
VAULT_ROOT = Path("/Users/jeffliu/Documents/A05_Obsidian Vault")
INDEX_DIR = VAULT_ROOT / "300 LLM-Wiki" / ".ai_index"
DB_DIR = INDEX_DIR / "chroma_db"
GRAPH_DB = INDEX_DIR / "wiki_graph.db"

if not DB_DIR.exists():
    print("尚未建立索引，請先執行 ingest_wiki.py")
    exit(1)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    exit(1)

gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=api_key, model_name="models/text-embedding-004")
chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
collection = chroma_client.get_collection(
    name="llm_wiki_cards", 
    embedding_function=gemini_ef
)

def search_semantic(query_text, limit=3):
    print(f"🔍 語意搜尋：'{query_text}'")
    results = collection.query(
        query_texts=[query_text],
        n_results=limit
    )
    
    if not results['documents'] or not results['documents'][0]:
        print("沒有找到相關資料。\n")
        return
        
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        filename = meta.get('filename')
        print(f"\n📄 關聯文獻: {filename} (距離: {dist:.4f})")
        print(f"📝 摘要:\n{doc}")

def search_graph(entity_name):
    print(f"\n🕸️ 圖譜關聯查詢：'{entity_name}'")
    if not GRAPH_DB.exists():
        print("尚未建立圖譜資料。")
        return
        
    conn = sqlite3.connect(str(GRAPH_DB))
    cursor = conn.cursor()
    # 模糊比對 主詞 或 受詞
    cursor.execute('''
        SELECT subject, predicate, object, source_file
        FROM graph_edges 
        WHERE subject LIKE ? OR object LIKE ?
        LIMIT 10
    ''', (f'%{entity_name}%', f'%{entity_name}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print(f"沒有找到與 '{entity_name}' 相關的圖譜規則。\n")
        return
        
    for r in rows:
        print(f"- [{r[0]}] --({r[1]})--> [{r[2]}]  (來源: {r[3]})")
    print()

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "預設測試搜尋：O-RAN 或 Telecom"
    
    print("====================================")
    search_semantic(query)
    
    # Extract naive keyword for graph testing
    possible_entities = query.split()
    if possible_entities:
        search_graph(possible_entities[0])
    print("====================================")
