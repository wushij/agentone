"""app/services/rag/parser.py — 文档解析与文本提取模块"""

from __future__ import annotations

from pathlib import Path


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
