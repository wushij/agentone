"""backend/app/services/rag_service.py"""
from __future__ import annotations

import json
import math
import os
import re
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
        file_path = _UPLOADS_DIR / file_name
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
        
        for idx, text_chunk in enumerate(chunks):
            vector = await get_embedding(text_chunk, api_key, base_url, model)
            store["chunks"].append({
                "id": f"chunk_{kb_id}_{file_id}_{idx}",
                "kbId": kb_id,
                "fileId": file_id,
                "fileName": file_name,
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
        for c in kb_chunks:
            vector_score = cosine_similarity(query_vector, c["vector"])
            lexical_score = keyword_score(query, c["text"])
            score = _blend_retrieval_score(vector_score, lexical_score, retrieval_mode)
            if score >= score_threshold:
                fid = c.get("fileId", "")
                orig_name = file_name_map.get(fid) or c.get("fileName", "")
                results.append({
                    "text": c["text"],
                    "score": score,
                    "fileName": orig_name,
                    "fileId": fid,
                    "index": c.get("index", 1),
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    @staticmethod
    async def fetch_kb_chunks_multi(
        kb_ids: list[str],
        query: str,
        *,
        max_total: int = 15,
    ) -> list[dict]:
        """Retrieve from one or more knowledge bases and merge by relevance score."""
        unique_ids: list[str] = []
        for kid in kb_ids:
            s = str(kid).strip()
            if s and s not in unique_ids:
                unique_ids.append(s)
        if not unique_ids:
            return []

        from app.api.knowledge import _load_kb

        kb_list = _load_kb()
        kb_name_map = {k["id"]: k.get("name", k["id"]) for k in kb_list}

        merged: list[dict] = []
        for kb_id in unique_ids:
            chunks = await RagService.fetch_kb_chunks(kb_id, query)
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
        return results[:cap]

    @staticmethod
    async def fetch_kb_chunks(kb_id: str, query: str) -> list[dict]:
        """Load KB config and run vector retrieval for chat."""
        from app.api.knowledge import _load_kb
        from app.db.session import SessionLocal
        from app.services.model_service import ModelService

        kb_list = _load_kb()
        kb_cfg = next((k for k in kb_list if k["id"] == kb_id), None)
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
        file_path = _UPLOADS_DIR / stored_filename
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
