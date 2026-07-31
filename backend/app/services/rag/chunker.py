"""app/services/rag/chunker.py — 文本切片与分块处理模块"""

from __future__ import annotations

SEGMENT_DELIMITERS: dict[str, str] = {
    "newline": "\n",
    "paragraph": "\n\n",
    "none": "",
}


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
