"""LLM-Wiki 共用 embedding：卡片索引與查詢必須使用同一個模型。
模型服務：Spark 上的 Ollama（只綁 Tailscale），位址從 .env 的 OLLAMA_EMBED_URL 讀取。"""
import json, os, urllib.request
from chromadb.utils import embedding_functions

EMBED_MODEL = "qwen3-embedding:4b"


def embed_texts(texts, timeout=120):
    url = os.environ.get("OLLAMA_EMBED_URL")
    if not url:
        raise RuntimeError("OLLAMA_EMBED_URL not set (must-output-brain/.env)")
    req = urllib.request.Request(f"{url.rstrip('/')}/api/embed",
        data=json.dumps({"model": EMBED_MODEL, "input": list(texts)}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["embeddings"]


class OllamaEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __call__(self, input):
        return embed_texts(input)

    def name(self):
        return "OllamaEmbeddingFunction"
