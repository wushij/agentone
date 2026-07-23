"""app/knowledge/loaders/docx.py"""

from pathlib import Path
from typing import Any


class DocxLoader:
    def load(self, path: Path) -> list[dict[str, Any]]:
        from app.services.rag.rag_service import extract_file_text

        text = extract_file_text(path)
        return [{"text": text, "metadata": {"source": str(path), "filename": path.name, "type": "docx"}}]
