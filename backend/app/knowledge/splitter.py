"""app/knowledge/splitter.py — 文本分割器（复用 rag_service.split_text）"""

from typing import Any

from app.services.rag.rag_service import split_text


class TextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue
            parts = split_text(text, self.chunk_size, self.chunk_overlap)
            meta = doc.get("metadata", {})
            for i, part in enumerate(parts):
                chunks.append({"text": part, "metadata": {**meta, "chunk_index": i}})
        return chunks
