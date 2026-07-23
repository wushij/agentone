"""app/services/embedding.py — 嵌入服务"""

from typing import Any


class EmbeddingService:
    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 1536 for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * 1536