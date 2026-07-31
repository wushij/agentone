"""backend/app/services/rag_service.py"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
import httpx

from app.storage import data_root, uploads_dir, vector_store_json


def _load_vector_store() -> dict:
    path = vector_store_json()
    if not path.exists():
        return {"chunks": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"chunks": []}


def _save_vector_store(store: dict):
    data_root()
    path = vector_store_json()
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


async def _invalidate_rag_cache(kb_id: str) -> None:
    """主动失效（§8.3）：文档变更后 bump 该库版本。"""
    try:
        from app.cache import RagCache

        await RagCache().bump_version(kb_id)
    except Exception:
        pass


def _invalidate_rag_cache_sync(kb_id: str) -> None:
    """同步上下文调用（remove/clear）：尽力失效缓存，不阻断主流程。"""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_invalidate_rag_cache(kb_id))
    except RuntimeError:
        try:
            asyncio.run(_invalidate_rag_cache(kb_id))
        except Exception:
            pass


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


SEGMENT_DELIMITERS: dict[str, str] = {
    "newline": "\n",
    "paragraph": "\n\n",
    "none": "",
}


def split_text_segments(
    text: str,
    *,
    delimiter: str = "paragraph",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """Coze-style segmentation: split by delimiter first, then cap by max length."""
    if not text or not text.strip():
        return []

    sep = SEGMENT_DELIMITERS.get(delimiter, "\n\n")
    if not sep:
        return split_text(text, chunk_size, chunk_overlap)

    raw_parts = [p.strip() for p in text.split(sep) if p.strip()]
    if not raw_parts:
        return []

    chunks: list[str] = []
    for part in raw_parts:
        if len(part) <= chunk_size:
            chunks.append(part)
        else:
            chunks.extend(split_text(part, chunk_size, chunk_overlap))
    return chunks


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

    # If no key, generate a deterministic fallback mock vector
    if not api_key:
        vector = _generate_mock_vector(text)
    else:
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

    # 回填缓存
    if cache is not None:
        for i in miss_idx:
            key = keys[i]
            if key and results[i] is not None:
                try:
                    await cache.set(key, results[i])
                except Exception:
                    pass

    return [r if r is not None else _generate_mock_vector(texts[i]) for i, r in enumerate(results)]


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


_QUERY_ALIASES = (
    ("aimes", "ai-mes"),
    ("ames", "ai-mes"),
    ("ai mes", "ai-mes"),
)
_KEYWORD_STOPWORDS = frozenset({
    "什么", "是什么", "怎么", "如何", "哪些", "为什么", "能否", "可以", "吗", "呢", "的", "了", "啊",
})


def _normalize_query_text(text: str) -> str:
    normalized = text.lower().strip()
    for src, dst in _QUERY_ALIASES:
        normalized = normalized.replace(src, dst)
    return normalized


def keyword_score(query: str, text: str) -> float:
    """Lexical overlap score for mock / fulltext retrieval."""
    query_norm = _normalize_query_text(query)
    text_norm = _normalize_query_text(text)
    if not query_norm:
        return 0.0

    raw_tokens = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9\-]+", query_norm)
    tokens: list[str] = []
    for token in raw_tokens:
        if token in _KEYWORD_STOPWORDS or len(token) < 2:
            continue
        tokens.append(token)
        for suffix in ("是什么", "有哪些", "怎么样", "如何"):
            if token.endswith(suffix) and len(token) > len(suffix) + 1:
                stem = token[: -len(suffix)]
                if stem not in _KEYWORD_STOPWORDS and len(stem) >= 2:
                    tokens.append(stem)

    tokens = list(dict.fromkeys(tokens))
    if not tokens:
        compact = query_norm
        for stop in _KEYWORD_STOPWORDS:
            compact = compact.replace(stop, "")
        compact = re.sub(r"[\s\?？!！,，.。:：;；]+", "", compact)
        return 1.0 if compact and compact in text_norm else 0.0

    hits = sum(1 for token in tokens if token in text_norm)
    return hits / len(tokens)


def _blend_retrieval_score(
    vector_score: float,
    lexical_score: float,
    retrieval_mode: str,
) -> float:
    mode = (retrieval_mode or "hybrid").lower()
    if mode == "fulltext":
        return lexical_score
    if mode == "vector":
        return vector_score
    return max(vector_score, lexical_score)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _tokenize_bm25(text: str) -> list[str]:
    norm = _normalize_query_text(text)
    tokens = re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9\-]+", norm)
    return [t for t in tokens if t not in _KEYWORD_STOPWORDS]


def bm25_scores(query: str, docs: list[str], *, k1: float = 1.5, b: float = 0.75) -> list[float]:
    """真 BM25 打分（中文按字 + 英文按词元）。"""
    if not docs:
        return []
    q_tokens = [t for t in dict.fromkeys(_tokenize_bm25(query))]
    doc_tokens = [_tokenize_bm25(d) for d in docs]
    doc_len = [len(t) for t in doc_tokens]
    avgdl = (sum(doc_len) / len(doc_len)) if doc_len else 0.0
    N = len(docs)
    # df
    df: dict[str, int] = {}
    for toks in doc_tokens:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    scores = [0.0] * N
    for i, toks in enumerate(doc_tokens):
        if not toks:
            continue
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        dl = doc_len[i]
        for qt in q_tokens:
            if qt not in tf:
                continue
            n_qt = df.get(qt, 0)
            idf = math.log(1 + (N - n_qt + 0.5) / (n_qt + 0.5))
            freq = tf[qt]
            denom = freq + k1 * (1 - b + b * (dl / avgdl if avgdl else 1))
            scores[i] += idf * (freq * (k1 + 1)) / (denom or 1)
    return scores


def rrf_fuse(*rankings: list[int], k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion：输入若干"按分数降序的文档索引列表"，输出 idx→融合分。"""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return fused


async def _qdrant_retrieve(
    kb_id: str, query: str, query_vector: list[float], top_k: int
) -> list[dict] | None:
    """Qdrant 启用时的检索（§8.1）：ANN 召回候选 → BM25 词法分 → RRF 融合 → Reranker。

    返回 None 表示 Qdrant 未启用/无命中 → 由 query_kb 回退 JSON 向量库。
    """
    try:
        from app.knowledge.stores.qdrant import get_qdrant_store

        qs = get_qdrant_store()
    except Exception:
        qs = None
    if qs is None:
        return None
    try:
        candidates = await qs.search(kb_id, query_vector, top_k=max(top_k * 5, 20))
    except Exception:
        return None
    if not candidates:
        return None

    # 原始文件名映射（DB original_name 优先）
    fids = {c.get("fileId") for c in candidates if c.get("fileId")}
    name_map: dict = {}
    if fids:
        from app.db.session import SessionLocal
        from app.models.file_asset import FileAsset
        from sqlalchemy import select

        db = SessionLocal()
        try:
            rows = db.execute(
                select(FileAsset.id, FileAsset.original_name).where(FileAsset.id.in_(fids))
            ).all()
            name_map = {r[0]: r[1] for r in rows}
        except Exception:
            pass
        finally:
            db.close()

    texts = [c["text"] for c in candidates]
    vec_scores = [c["score"] for c in candidates]
    lex_scores = bm25_scores(query, texts)
    vec_rank = sorted(range(len(candidates)), key=lambda i: vec_scores[i], reverse=True)
    lex_rank = sorted(range(len(candidates)), key=lambda i: lex_scores[i], reverse=True)
    fused = rrf_fuse(vec_rank, lex_rank)
    max_fused = max(fused.values()) if fused else 1.0

    merged: list[dict] = []
    for i, c in enumerate(candidates):
        fid = c.get("fileId", "")
        merged.append({
            "text": c["text"],
            "score": round(fused.get(i, 0.0) / (max_fused or 1.0), 4),
            "vectorScore": round(vec_scores[i], 4),
            "bm25Score": round(lex_scores[i], 4),
            "fileName": name_map.get(fid) or c.get("fileName", ""),
            "fileId": fid,
            "index": 1,
        })
    merged.sort(key=lambda x: x["score"], reverse=True)

    try:
        from app.knowledge.reranker import get_reranker

        cand = merged[: max(top_k * 3, top_k)]
        if len(cand) > 1:
            return get_reranker().rerank(query, cand, top_k=top_k)
    except Exception:
        pass
    return merged[:top_k]


class RagService:
    @staticmethod
    async def index_file_in_kb(
        kb_id: str,
        file_id: str,
        file_name: str,
        chunk_size: int,
        chunk_overlap: int,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "text-embedding-3-small",
        segment_delimiter: str = "paragraph",
    ):
        file_path = uploads_dir() / file_name
        if not file_path.exists():
            return

        text = extract_file_text(file_path)
        chunks = split_text_segments(
            text,
            delimiter=segment_delimiter,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        # Load store
        store = _load_vector_store()
        
        # Remove existing chunks for this file under this kb
        store["chunks"] = [c for c in store["chunks"] if not (c["kbId"] == kb_id and c["fileId"] == file_id)]

        # 批量 embedding（§8.1）：一次 API 调用处理全部分段，而非逐条
        vectors = await get_embeddings_batch(chunks, api_key, base_url, model)
        for idx, (text_chunk, vector) in enumerate(zip(chunks, vectors)):
            store["chunks"].append({
                "id": f"chunk_{kb_id}_{file_id}_{idx}",
                "kbId": kb_id,
                "fileId": file_id,
                "fileName": file_name,
                "text": text_chunk,
                "vector": vector
            })

        _save_vector_store(store)

        # Qdrant 后端（§8.1）：启用时同步 upsert（JSON 仍保留为回退与词法检索源）
        try:
            from app.knowledge.stores.qdrant import get_qdrant_store

            qs = get_qdrant_store()
            if qs is not None:
                import hashlib

                points = []
                for idx, (text_chunk, vector) in enumerate(zip(chunks, vectors)):
                    pid = int(hashlib.sha1(f"{kb_id}_{file_id}_{idx}".encode()).hexdigest()[:15], 16)
                    points.append({
                        "id": pid,
                        "vector": vector,
                        "payload": {"kbId": kb_id, "fileId": file_id, "fileName": file_name, "text": text_chunk},
                    })
                if points:
                    await qs.upsert(points)
        except Exception:
            pass
        await _invalidate_rag_cache(kb_id)

    @staticmethod
    def remove_file_chunks(kb_id: str, file_id: str):
        store = _load_vector_store()
        store["chunks"] = [c for c in store["chunks"] if not (c["kbId"] == kb_id and c["fileId"] == file_id)]
        _save_vector_store(store)
        _invalidate_rag_cache_sync(kb_id)

    @staticmethod
    def clear_kb_chunks(kb_id: str):
        store = _load_vector_store()
        store["chunks"] = [c for c in store["chunks"] if c["kbId"] != kb_id]
        _save_vector_store(store)
        _invalidate_rag_cache_sync(kb_id)

    @staticmethod
    async def query_kb(
        kb_id: str,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.5,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "text-embedding-3-small",
        retrieval_mode: str = "hybrid",
    ) -> list[dict]:
        store = _load_vector_store()
        kb_chunks = [c for c in store["chunks"] if c["kbId"] == kb_id]
        if not kb_chunks:
            return []

        query_vector = await get_embedding(query, api_key, base_url, model)

        # Qdrant 向量后端（§8.1）：启用且命中时走 ANN；否则回退下方 JSON 暴力检索
        qdrant_hits = await _qdrant_retrieve(kb_id, query, query_vector, top_k)
        if qdrant_hits is not None:
            return qdrant_hits

        # 批量加载匹配到的文件 ID 对应的真实原始文件名
        file_ids = {c.get("fileId") for c in kb_chunks if c.get("fileId")}
        file_name_map = {}
        if file_ids:
            from app.db.session import SessionLocal
            from app.models.file_asset import FileAsset
            from sqlalchemy import select
            db = SessionLocal()
            try:
                stmt = select(FileAsset.id, FileAsset.original_name).where(FileAsset.id.in_(file_ids))
                rows = db.execute(stmt).all()
                file_name_map = {row[0]: row[1] for row in rows}
            except Exception:
                pass
            finally:
                db.close()

        results = []
        texts = [c["text"] for c in kb_chunks]
        mode = (retrieval_mode or "hybrid").lower()

        if mode == "hybrid":
            # 真混合检索：向量余弦 + BM25，RRF 融合（§8.4）
            vec_scores = [cosine_similarity(query_vector, c["vector"]) for c in kb_chunks]
            lex_scores = bm25_scores(query, texts)
            vec_rank = sorted(range(len(kb_chunks)), key=lambda i: vec_scores[i], reverse=True)
            lex_rank = sorted(range(len(kb_chunks)), key=lambda i: lex_scores[i], reverse=True)
            fused = rrf_fuse(vec_rank, lex_rank)
            max_fused = max(fused.values()) if fused else 1.0
            for i, c in enumerate(kb_chunks):
                # 归一化融合分到 0~1，便于沿用 score_threshold 语义
                norm = fused.get(i, 0.0) / (max_fused or 1.0)
                # 命中任一通道（向量或词法有信号）才保留，避免全库低分噪声
                if vec_scores[i] < score_threshold and lex_scores[i] <= 0:
                    continue
                fid = c.get("fileId", "")
                results.append({
                    "text": c["text"],
                    "score": round(norm, 4),
                    "vectorScore": round(vec_scores[i], 4),
                    "bm25Score": round(lex_scores[i], 4),
                    "fileName": file_name_map.get(fid) or c.get("fileName", ""),
                    "fileId": fid,
                    "index": c.get("index", 1),
                })
            results.sort(key=lambda x: x["score"], reverse=True)
        else:
            for c in kb_chunks:
                vector_score = cosine_similarity(query_vector, c["vector"])
                lexical_score = keyword_score(query, c["text"])
                score = _blend_retrieval_score(vector_score, lexical_score, retrieval_mode)
                if score >= score_threshold:
                    fid = c.get("fileId", "")
                    results.append({
                        "text": c["text"],
                        "score": score,
                        "fileName": file_name_map.get(fid) or c.get("fileName", ""),
                        "fileId": fid,
                        "index": c.get("index", 1),
                    })
            results.sort(key=lambda x: x["score"], reverse=True)

        # 真 Reranker 精排（候选取 top_k*3 交给重排，§8.4）
        try:
            from app.knowledge.reranker import get_reranker

            candidates = results[: max(top_k * 3, top_k)]
            if len(candidates) > 1:
                results = get_reranker().rerank(query, candidates, top_k=top_k)
                return results
        except Exception:
            pass
        return results[:top_k]

    @staticmethod
    async def fetch_kb_chunks_multi(
        kb_ids: list[str],
        query: str,
        *,
        max_total: int = 15,
        history: list | None = None,
    ) -> list[dict]:
        """Retrieve from one or more knowledge bases and merge by relevance score.

        流程（§8.2 §8.3）：L1 结果缓存 → 未命中则 Query Transform（按库配置）
        → 多查询并行检索 → RRF 已在 query_kb 内完成 → 去重合并 → 回填缓存。
        """
        unique_ids: list[str] = []
        for kid in kb_ids:
            s = str(kid).strip()
            if s and s not in unique_ids:
                unique_ids.append(s)
        if not unique_ids:
            return []

        from app.services.rag.kb_store import load_all

        kb_list = load_all()
        kb_name_map = {k["id"]: k.get("name", k["id"]) for k in kb_list}

        # L1 结果缓存（§8.3）+ 命中率指标
        cache = None
        cache_key = ""
        try:
            from app.cache import RagCache
            from app.monitor.metrics import get_metrics

            cache = RagCache()
            cache_key = await cache.make_key(kb_ids=unique_ids, query=query)
            cached = await cache.get(cache_key)
            if cached is not None:
                get_metrics().record_cache("rag_result", hit=True)
                return cached
            get_metrics().record_cache("rag_result", hit=False)
        except Exception:
            cache = None

        # Query Transform（§8.2）：取各库配置的并集作为启用模式
        transform_modes: list[str] = []
        for kb in kb_list:
            if kb["id"] in unique_ids:
                modes = kb.get("queryTransform") or []
                if isinstance(modes, list):
                    transform_modes.extend(modes)
        queries = [query]
        if transform_modes:
            try:
                from app.knowledge.transform import transform_query

                queries = await transform_query(query, list(dict.fromkeys(transform_modes)), history)
            except Exception:
                queries = [query]

        merged: list[dict] = []
        for kb_id in unique_ids:
            for q in queries:
                chunks = await RagService.fetch_kb_chunks(kb_id, q)
                for chunk in chunks:
                    merged.append({
                        **chunk,
                        "kbId": kb_id,
                        "kbName": kb_name_map.get(kb_id, kb_id),
                    })

        best_by_text: dict[str, dict] = {}
        for chunk in merged:
            text = (chunk.get("text") or "").strip()
            if not text:
                continue
            prev = best_by_text.get(text)
            if prev is None or chunk.get("score", 0) > prev.get("score", 0):
                best_by_text[text] = chunk

        results = sorted(best_by_text.values(), key=lambda x: x.get("score", 0), reverse=True)
        cap = min(max_total, max(3, len(unique_ids) * 3))
        results = results[:cap]

        if cache is not None and cache_key:
            try:
                await cache.set(cache_key, results)
            except Exception:
                pass
        return results

    @staticmethod
    async def fetch_kb_chunks(kb_id: str, query: str) -> list[dict]:
        """Load KB config and run vector retrieval for chat."""
        from app.db.session import SessionLocal
        from app.services.llm.model_service import ModelService
        from app.services.rag.kb_store import get_kb

        kb_cfg = get_kb(kb_id)
        if not kb_cfg:
            return []

        top_k = int(kb_cfg.get("topK", 3))
        score_threshold = float(kb_cfg.get("scoreThreshold", 0.5))
        retrieval_mode = kb_cfg.get("retrievalMode", "hybrid")

        db = SessionLocal()
        try:
            model_service = ModelService(db)
            default_model = model_service.get_default()
            api_key = default_model.api_key if default_model else None
            base_url = default_model.base_url if default_model else None
            model_name = default_model.model_name if default_model else "text-embedding-3-small"
        finally:
            db.close()

        return await RagService.query_kb(
            kb_id=kb_id,
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            retrieval_mode=retrieval_mode,
        )

    @staticmethod
    def build_file_preview_segments(
        file_id: str,
        stored_filename: str,
        *,
        display_name: str | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        segment_delimiter: str = "paragraph",
    ) -> list[dict]:
        file_path = uploads_dir() / stored_filename
        if not file_path.exists():
            return []

        label = display_name or stored_filename
        texts = split_text_segments(
            extract_file_text(file_path),
            delimiter=segment_delimiter,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        segments: list[dict] = []
        for idx, text in enumerate(texts, 1):
            segments.append({
                "id": f"preview_{file_id}_{idx}",
                "fileId": file_id,
                "fileName": label,
                "index": idx,
                "charCount": len(text),
                "text": text,
            })
        return segments

    @staticmethod
    def list_indexed_segments(kb_id: str) -> list[dict]:
        store = _load_vector_store()
        kb_chunks = [c for c in store["chunks"] if c["kbId"] == kb_id]
        segments: list[dict] = []
        for idx, chunk in enumerate(kb_chunks, 1):
            segments.append({
                "id": chunk.get("id", f"chunk_{idx}"),
                "fileId": chunk.get("fileId", ""),
                "fileName": chunk.get("fileName", ""),
                "index": idx,
                "charCount": len(chunk.get("text", "")),
                "text": chunk.get("text", ""),
                "source": "indexed",
            })
        return segments


def _parse_qa_text(text: str) -> tuple[str, str] | None:
    normalized = text.replace("\r\n", "\n").strip()
    q_match = re.match(r"^问[:：]\s*([\s\S]*?)(?:\n答[:：]|$)", normalized)
    a_match = re.search(r"答[:：]\s*([\s\S]*)$", normalized)
    if not q_match and not a_match:
        return None
    question = (q_match.group(1) if q_match else "").strip()
    answer = (a_match.group(1) if a_match else "").strip()
    return question, answer


def format_kb_retrieve_answer(user_query: str, chunks: list[dict]) -> str:
    """Return retrieved chunk text in a beautifully structured Markdown format."""
    if not chunks:
        return "❌ 未在知识库中找到相关内容，请换个问法或调低匹配阈值后重试。"

    lines: list[str] = [
        "💡 **直检结果（未启用大模型总结）**",
        f"为您检索到以下 **{len(chunks)}** 条最相关的知识库分段：\n"
    ]

    for idx, chunk in enumerate(chunks, 1):
        filename = chunk.get("fileName", "未知文件")
        kb_name = chunk.get("kbName", "默认知识库")
        score = chunk.get("score")
        score_str = f" (匹配度: {score:.2f})" if isinstance(score, (int, float)) else ""
        content = chunk.get("text", "").strip()
        if not content:
            continue

        lines.append(f"### 📄 来源 {idx}：`{filename}`{score_str}")
        lines.append(f"> **知识库**：{kb_name}")

        # Parse QA if it matches
        qa = _parse_qa_text(content)
        if qa:
            lines.append(">")
            lines.append(f"> ❓ **问**：{qa[0]}")
            lines.append(f"> 💡 **答**：{qa[1] if qa[1] else '(暂无回答)'}")
        else:
            # Wrap content lines in blockquote
            indented_content = "\n".join(f"> {line}" for line in content.split("\n"))
            lines.append(indented_content)

        lines.append("\n---")

    return "\n".join(lines)
