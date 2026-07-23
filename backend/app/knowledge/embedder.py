"""app/knowledge/embedder.py — 向量嵌入器（复用 rag_service.get_embedding）"""

from typing import Any

from app.services.rag.rag_service import get_embedding
from app.config.settings import get_settings


class Embedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or None
        base_url = getattr(settings, "DEEPSEEK_BASE_URL", None)
        vectors: list[list[float]] = []
        for text in texts:
            vectors.append(
                await get_embedding(text, api_key=api_key, base_url=base_url, model=self.model)
            )
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed([text])
        return vectors[0]
