"""app/services/rag/embedder.py — Embedding 生成与 Mock 向量提取模块"""

from __future__ import annotations

import math
import httpx


def _generate_mock_vector(text: str, dimensions: int = 1536) -> list[float]:
    """根据字符分布生成确定性的模拟高维向量"""
    vector = [0.0] * dimensions
    for idx, char in enumerate(text[:dimensions]):
        vector[idx % dimensions] += ord(char)
    sq_sum = sum(x * x for x in vector)
    if sq_sum > 0:
        norm = math.sqrt(sq_sum)
        vector = [x / norm for x in vector]
    else:
        vector = [0.0] * dimensions
        vector[0] = 1.0
    return vector


async def get_embedding(
    text: str,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = "text-embedding-3-small",
) -> list[float]:
    try:
        from app.cache import EmbeddingCache

        cache = EmbeddingCache()
        cache_key = EmbeddingCache.make_key(model=model, text=text)
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
    except Exception:
        cache = None
        cache_key = ""

    if not api_key:
        vector = _generate_mock_vector(text)
    else:
        url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {"input": text, "model": model}
        vector = _generate_mock_vector(text)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    vector = data["data"][0]["embedding"]
        except Exception:
            pass

    try:
        if cache is not None and cache_key:
            await cache.set(cache_key, vector)
    except Exception:
        pass
    return vector


async def get_embeddings_batch(
    texts: list[str],
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = "text-embedding-3-small",
    *,
    batch_size: int = 64,
) -> list[list[float]]:
    """批量 embedding（§8.1）：先查缓存，未命中的按 batch 合并一次 API 调用。"""
    if not texts:
        return []
    try:
        from app.cache import EmbeddingCache

        cache = EmbeddingCache()
    except Exception:
        cache = None

    results: list[list[float] | None] = [None] * len(texts)
    miss_idx: list[int] = []
    keys: list[str] = []
    for i, text in enumerate(texts):
        key = ""
        if cache is not None:
            try:
                key = EmbeddingCache.make_key(model=model, text=text)
                cached = await cache.get(key)
                if cached is not None:
                    results[i] = cached
                    keys.append(key)
                    continue
            except Exception:
                key = ""
        keys.append(key)
        miss_idx.append(i)

    if not miss_idx:
        return [r or _generate_mock_vector(texts[i]) for i, r in enumerate(results)]

    if not api_key:
        for i in miss_idx:
            results[i] = _generate_mock_vector(texts[i])
    else:
        url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/embeddings"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        for start in range(0, len(miss_idx), batch_size):
            batch = miss_idx[start : start + batch_size]
            payload = {"input": [texts[i] for i in batch], "model": model}
            vectors = None
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        vectors = [item["embedding"] for item in sorted(data, key=lambda x: x.get("index", 0))]
            except Exception:
                vectors = None
            for offset, i in enumerate(batch):
                if vectors and offset < len(vectors):
                    results[i] = vectors[offset]
                else:
                    results[i] = _generate_mock_vector(texts[i])

    if cache is not None:
        for i in miss_idx:
            key = keys[i]
            if key and results[i] is not None:
                try:
                    await cache.set(key, results[i])
                except Exception:
                    pass

    return [r if r is not None else _generate_mock_vector(texts[i]) for i, r in enumerate(results)]
