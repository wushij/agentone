"""backend/app/services/rag/rag_service.py — RAG 核心检索服务"""

from __future__ import annotations

import json
import math
import os
import re
import asyncio
from pathlib import Path

import httpx

from app.storage import data_root, uploads_dir, vector_store_json
from app.utils.logger import logger

# 从拆分的子模块导入子工具函数
from app.services.rag.chunker import SEGMENT_DELIMITERS, split_text, split_text_segments
from app.services.rag.embedder import _generate_mock_vector, get_embedding, get_embeddings_batch
from app.services.rag.json_store import (
    invalidate_rag_cache,
    invalidate_rag_cache_sync,
    load_vector_store,
    save_vector_store,
)
from app.services.rag.parser import extract_file_text

# 别名导出，确保向下兼容
_load_vector_store = load_vector_store
_save_vector_store = save_vector_store
_invalidate_rag_cache = invalidate_rag_cache
_invalidate_rag_cache_sync = invalidate_rag_cache_sync

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
    """改进版中文 BM25 分词器：提取英文/数字词元 + 中文 2-gram/3-gram 词组与实体，避免单字泛化混淆。"""
    norm = _normalize_query_text(text)
    tokens: list[str] = []

    # 1. 提取英文/数字/连字符词元
    en_tokens = re.findall(r"[a-zA-Z0-9\-]+", norm)
    for t in en_tokens:
        if len(t) >= 2 and t not in _KEYWORD_STOPWORDS:
            tokens.append(t)

    # 2. 提取连续中文词组段落并做 2-gram / 3-gram 及整词拆分
    cn_segments = re.findall(r"[\u4e00-\u9fff]+", norm)
    for seg in cn_segments:
        if seg not in _KEYWORD_STOPWORDS and len(seg) >= 2:
            tokens.append(seg)
        for i in range(len(seg) - 1):
            bi = seg[i : i + 2]
            if bi not in _KEYWORD_STOPWORDS:
                tokens.append(bi)
        for i in range(len(seg) - 2):
            tri = seg[i : i + 3]
            if tri not in _KEYWORD_STOPWORDS:
                tokens.append(tri)

    return [t for t in dict.fromkeys(tokens)]


def bm25_scores(query: str, docs: list[str], *, k1: float = 1.5, b: float = 0.75) -> list[float]:
    """真 BM25 打分（中文按 2-gram/3-gram 词组 + 英文按词元）。"""
    if not docs:
        return []
    q_tokens = [t for t in dict.fromkeys(_tokenize_bm25(query))]
    doc_tokens = [_tokenize_bm25(d) for d in docs]
    doc_len = [len(t) for t in doc_tokens]
    avgdl = (sum(doc_len) / len(doc_len)) if doc_len else 0.0
    N = len(docs)
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


def hybrid_blend(
    vec_scores: list[float],
    lex_scores: list[float],
    *,
    w_lex: float = 0.7,
    texts: list[str] | None = None,
    query: str | None = None,
) -> list[float]:
    """分数加权混合（BM25 词法主导）：归一化后 w_lex*BM25 + (1-w_lex)*向量。

    当包含精准文本/提问全字匹配时，自动提升匹配度至 0.98+。
    """
    n = len(lex_scores)
    if n == 0:
        return []
    max_lex = max(lex_scores) if lex_scores else 0.0
    pos_vec = [max(0.0, v) for v in vec_scores] if vec_scores else [0.0] * n
    max_vec = max(pos_vec) if pos_vec else 0.0

    q_clean = ""
    if query:
        q_clean = re.sub(r"[\s\?？!！,，.。:：;；]+", "", query.lower())

    blended: list[float] = []
    for i in range(n):
        nl = (lex_scores[i] / max_lex) if max_lex > 0 else 0.0
        nv = (pos_vec[i] / max_vec) if max_vec > 0 else 0.0
        if max_lex > 0 and lex_scores[i] == 0:
            final_score = nv * 0.15
        else:
            final_score = w_lex * nl + (1 - w_lex) * nv

        # 文本提问精准匹配或高置信度 BM25 全命中加成
        if q_clean and texts and i < len(texts):
            t_clean = re.sub(r"[\s\?？!！,，.。:：;；]+", "", texts[i].lower())
            if q_clean in t_clean:
                final_score = max(final_score, 0.98)
            elif nl == 1.0 and lex_scores[i] >= 20.0:
                final_score = max(final_score, 0.95)

        blended.append(round(final_score, 4))
    return blended


async def _qdrant_retrieve(
    kb_id: str, query: str, query_vector: list[float], top_k: int, score_threshold: float = 0.5
) -> list[dict] | None:
    """Qdrant 检索（双路召回增强）：ANN 向量召回 + 全局 BM25 词法召回 → 候选融合 → 阈值过滤 → Reranker。"""
    try:
        from app.knowledge.stores.qdrant import get_qdrant_store

        qs = get_qdrant_store()
    except Exception:
        qs = None

    qdrant_cands: list[dict] = []
    if qs is not None:
        try:
            qdrant_cands = await qs.search(kb_id, query_vector, top_k=max(top_k * 5, 20)) or []
        except Exception:
            qdrant_cands = []

    # 提取本地 JSON Store 中该 KB 的所有块，进行全局 BM25 补充召回，防止矢量偏离漏招精准文本匹配
    store = load_vector_store()
    kb_chunks = [c for c in store["chunks"] if c.get("kbId") == kb_id]

    if not qdrant_cands and not kb_chunks:
        return None

    candidate_map: dict[str, dict] = {}
    for c in qdrant_cands:
        text_key = (c.get("text") or "").strip()
        if text_key:
            candidate_map[text_key] = {
                "text": c["text"],
                "fileId": c.get("fileId", ""),
                "fileName": c.get("fileName", ""),
                "vectorScore": float(c.get("score", 0.0)),
            }

    if kb_chunks:
        all_texts = [c["text"] for c in kb_chunks]
        bm25_all = bm25_scores(query, all_texts)
        top_bm25_indices = sorted(range(len(bm25_all)), key=lambda i: bm25_all[i], reverse=True)[:12]
        for idx in top_bm25_indices:
            if bm25_all[idx] > 0:
                chunk = kb_chunks[idx]
                text_key = (chunk.get("text") or "").strip()
                if text_key not in candidate_map:
                    vec_score = cosine_similarity(query_vector, chunk.get("vector", []))
                    candidate_map[text_key] = {
                        "text": chunk["text"],
                        "fileId": chunk.get("fileId", ""),
                        "fileName": chunk.get("fileName", ""),
                        "vectorScore": vec_score,
                    }

    candidates = list(candidate_map.values())
    if not candidates:
        return None

    fids = {c.get("fileId") for c in candidates if c.get("fileId")}
    name_map: dict = {}
    if fids:
        from sqlalchemy import select

        from app.db.session import SessionLocal
        from app.models.file_asset import FileAsset

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
    vec_scores = [c["vectorScore"] for c in candidates]
    lex_scores = bm25_scores(query, texts)
    blended = hybrid_blend(vec_scores, lex_scores, texts=texts, query=query)

    merged: list[dict] = []
    for i, c in enumerate(candidates):
        fid = c.get("fileId", "")
        score_val = round(blended[i], 4)
        merged.append({
            "text": c["text"],
            "score": score_val,
            "vectorScore": round(vec_scores[i], 4),
            "bm25Score": round(lex_scores[i], 4),
            "fileName": name_map.get(fid) or c.get("fileName", ""),
            "fileId": fid,
            "index": 1,
        })
    merged.sort(key=lambda x: x["score"], reverse=True)

    # 动态阈值过滤：若包含高置信度全匹配（>= 0.90），收紧相对阈值至最高分的 76%，防止仅个别泛词重合的无关块凑数
    if merged:
        top_score = merged[0]["score"]
        cutoff_ratio = 0.76 if top_score >= 0.90 else 0.70
        cutoff = max(score_threshold, top_score * cutoff_ratio)
        merged = [r for r in merged if r["score"] >= cutoff]

    if not merged:
        return []

    try:
        from app.knowledge.reranker import get_reranker

        cand = merged[: max(top_k * 3, top_k)]
        if len(cand) > 1:
            reranked = await asyncio.to_thread(get_reranker().rerank, query, cand, top_k)
            if reranked:
                top_r = reranked[0]["score"]
                cutoff_r = max(score_threshold, top_r * (0.76 if top_r >= 0.90 else 0.70))
                reranked = [r for r in reranked if r["score"] >= cutoff_r]
            return reranked
    except Exception as exc:
        logger.warning(f"[RAG] 重排失败（已降级为融合分排序）: {exc}")
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

        store = load_vector_store()
        store["chunks"] = [c for c in store["chunks"] if not (c["kbId"] == kb_id and c["fileId"] == file_id)]

        vectors = await get_embeddings_batch(chunks, api_key, base_url, model)
        for idx, (text_chunk, vector) in enumerate(zip(chunks, vectors)):
            store["chunks"].append({
                "id": f"chunk_{kb_id}_{file_id}_{idx}",
                "kbId": kb_id,
                "fileId": file_id,
                "fileName": file_name,
                "text": text_chunk,
                "vector": vector,
            })

        save_vector_store(store)

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
        await invalidate_rag_cache(kb_id)

    @staticmethod
    def remove_file_chunks(kb_id: str, file_id: str):
        store = load_vector_store()
        store["chunks"] = [c for c in store["chunks"] if not (c["kbId"] == kb_id and c["fileId"] == file_id)]
        save_vector_store(store)
        invalidate_rag_cache_sync(kb_id)

    @staticmethod
    def clear_kb_chunks(kb_id: str):
        store = load_vector_store()
        store["chunks"] = [c for c in store["chunks"] if c["kbId"] != kb_id]
        save_vector_store(store)
        invalidate_rag_cache_sync(kb_id)

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
        store = load_vector_store()
        kb_chunks = [c for c in store["chunks"] if c["kbId"] == kb_id]
        if not kb_chunks:
            return []

        query_vector = await get_embedding(query, api_key, base_url, model)

        qdrant_hits = await _qdrant_retrieve(kb_id, query, query_vector, top_k, score_threshold=score_threshold)
        if qdrant_hits is not None:
            return qdrant_hits

        file_ids = {c.get("fileId") for c in kb_chunks if c.get("fileId")}
        file_name_map = {}
        if file_ids:
            from sqlalchemy import select

            from app.db.session import SessionLocal
            from app.models.file_asset import FileAsset

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
            vec_scores = [cosine_similarity(query_vector, c["vector"]) for c in kb_chunks]
            lex_scores = bm25_scores(query, texts)
            blended = hybrid_blend(vec_scores, lex_scores, texts=texts, query=query)
            for i, c in enumerate(kb_chunks):
                norm = blended[i]
                if norm < score_threshold or norm < 0.40:
                    continue
                if max(lex_scores) > 0 and lex_scores[i] <= 0 and vec_scores[i] < 0.85:
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
            if results:
                top_score = results[0]["score"]
                cutoff = max(score_threshold, top_score * 0.6)
                results = [r for r in results if r["score"] >= cutoff]
        else:
            for c in kb_chunks:
                vector_score = cosine_similarity(query_vector, c["vector"])
                lexical_score = keyword_score(query, c["text"])
                score = _blend_retrieval_score(vector_score, lexical_score, retrieval_mode)
                if score >= score_threshold and score >= 0.40:
                    fid = c.get("fileId", "")
                    results.append({
                        "text": c["text"],
                        "score": score,
                        "fileName": file_name_map.get(fid) or c.get("fileName", ""),
                        "fileId": fid,
                        "index": c.get("index", 1),
                    })
            results.sort(key=lambda x: x["score"], reverse=True)
            if results:
                top_score = results[0]["score"]
                cutoff = max(score_threshold, top_score * 0.6)
                results = [r for r in results if r["score"] >= cutoff]

        try:
            from app.knowledge.reranker import get_reranker

            candidates = results[: max(top_k * 3, top_k)]
            if len(candidates) > 1:
                # 修复（§4.6）：CPU 同步 predict 放线程，不阻塞事件循环
                results = await asyncio.to_thread(get_reranker().rerank, query, candidates, top_k)
                return results
        except Exception as exc:
            logger.warning(f"[RAG] 重排失败（已降级）: {exc}")
        return results[:top_k]

    @staticmethod
    async def fetch_kb_chunks_multi(
        kb_ids: list[str],
        query: str,
        *,
        max_total: int = 15,
        history: list | None = None,
    ) -> list[dict]:
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
        if results:
            top_score = results[0].get("score", 0)
            cutoff_ratio = 0.76 if top_score >= 0.90 else 0.70
            cutoff = max(0.50, top_score * cutoff_ratio)
            results = [r for r in results if r.get("score", 0) >= cutoff]

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
        store = load_vector_store()
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
    if not chunks:
        return "❌ 未在知识库中找到相关内容，请换个问法或调低匹配阈值后重试。"

    lines: list[str] = [
        "💡 **直检结果（未启用大模型总结）**",
        f"为您检索到以下 **{len(chunks)}** 条最相关的知识库分段：\n",
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

        qa = _parse_qa_text(content)
        if qa:
            lines.append(">")
            lines.append(f"> ❓ **问**：{qa[0]}")
            lines.append(f"> 💡 **答**：{qa[1] if qa[1] else '(暂无回答)'}")
        else:
            indented_content = "\n".join(f"> {line}" for line in content.split("\n"))
            lines.append(indented_content)

        lines.append("\n---")

    return "\n".join(lines)
