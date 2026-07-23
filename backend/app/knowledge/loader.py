"""app/knowledge/loader.py — 统一加载入口"""

from pathlib import Path
from typing import Any


def load_document(file_path: str | Path) -> list[dict[str, Any]]:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from app.knowledge.loaders.pdf import PdfLoader
        return PdfLoader().load(path)
    elif suffix in (".docx", ".doc"):
        from app.knowledge.loaders.docx import DocxLoader
        return DocxLoader().load(path)
    elif suffix in (".md", ".markdown"):
        from app.knowledge.loaders.markdown import MarkdownLoader
        return MarkdownLoader().load(path)
    else:
        from app.knowledge.loaders.text import TextLoader
        return TextLoader().load(path)