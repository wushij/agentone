"""backend/app/services/rag_service.py"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import httpx

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_VECTOR_STORE_JSON = _DATA_DIR / "vector_store.json"
_UPLOADS_DIR = _DATA_DIR / "uploads"


def _load_vector_store() -> dict:
    if not _VECTOR_STORE_JSON.exists():
        return {"chunks": []}
    try:
        return json.loads(_VECTOR_STORE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"chunks": []}


def _save_vector_store(store: dict):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _VECTOR_STORE_JSON.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
        if chunk_size - chunk_overlap <= 0:
            break
    return [c.strip() for c in chunks if c.strip()]


def extract_file_text(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext in [".txt", ".md"]:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text.append(t)
            return "\n".join(text)
        except Exception:
            return f"[PDF parsing fallback] Raw content placeholder for {file_path.name}"
    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception:
            return f"[Docx parsing fallback] Raw content placeholder for {file_path.name}"
    return f"[Unsupported File] {file_path.name}"


async def get_embedding(text: str, api_key: str | None = None, base_url: str | None = None, model: str = "text-embedding-3-small") -> list[float]:
    # If no key, generate a deterministic fallback mock vector
    if not api_key:
        return _generate_mock_vector(text)

    # Clean base url
    url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "input": text,
        "model": model
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
    except Exception:
        pass
    return _generate_mock_vector(text)


def _generate_mock_vector(text: str, dimensions: int = 1536) -> list[float]:
    # Deterministic mock embedding based on character counts
    vector = [0.0] * dimensions
    for idx, char in enumerate(text[:dimensions]):
        vector[idx % dimensions] += ord(char)
    # Normalize vector
    sq_sum = sum(x * x for x in vector)
    if sq_sum > 0:
        norm = math.sqrt(sq_sum)
        vector = [x / norm for x in vector]
    else:
        vector = [0.0] * dimensions
        vector[0] = 1.0
    return vector


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RagService:
    @staticmethod
    async def index_file_in_kb(kb_id: str, file_id: str, file_name: str, chunk_size: int, chunk_overlap: int, api_key: str | None = None, base_url: str | None = None, model: str = "text-embedding-3-small"):
        file_path = _UPLOADS_DIR / file_name
        if not file_path.exists():
            return

        text = extract_file_text(file_path)
        chunks = split_text(text, chunk_size, chunk_overlap)
        
        # Load store
        store = _load_vector_store()
        
        # Remove existing chunks for this file under this kb
        store["chunks"] = [c for c in store["chunks"] if not (c["kbId"] == kb_id and c["fileId"] == file_id)]
        
        for idx, text_chunk in enumerate(chunks):
            vector = await get_embedding(text_chunk, api_key, base_url, model)
            store["chunks"].append({
                "id": f"chunk_{kb_id}_{file_id}_{idx}",
                "kbId": kb_id,
                "fileId": file_id,
                "text": text_chunk,
                "vector": vector
            })
            
        _save_vector_store(store)

    @staticmethod
    def remove_file_chunks(kb_id: str, file_id: str):
        store = _load_vector_store()
        store["chunks"] = [c for c in store["chunks"] if not (c["kbId"] == kb_id and c["fileId"] == file_id)]
        _save_vector_store(store)

    @staticmethod
    def clear_kb_chunks(kb_id: str):
        store = _load_vector_store()
        store["chunks"] = [c for c in store["chunks"] if c["kbId"] != kb_id]
        _save_vector_store(store)

    @staticmethod
    async def query_kb(kb_id: str, query: str, top_k: int = 3, score_threshold: float = 0.5, api_key: str | None = None, base_url: str | None = None, model: str = "text-embedding-3-small") -> list[dict]:
        store = _load_vector_store()
        kb_chunks = [c for c in store["chunks"] if c["kbId"] == kb_id]
        if not kb_chunks:
            return []

        query_vector = await get_embedding(query, api_key, base_url, model)
        results = []
        for c in kb_chunks:
            sim = cosine_similarity(query_vector, c["vector"])
            if sim >= score_threshold:
                results.append({
                    "text": c["text"],
                    "score": sim
                })
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
