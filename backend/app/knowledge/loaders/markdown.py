"""app/knowledge/loaders/markdown.py"""

from pathlib import Path
from typing import Any


class MarkdownLoader:
    def load(self, path: Path) -> list[dict[str, Any]]:
        from app.services.rag.rag_service import extract_file_text

        text = extract_file_text(path)
        return [{"text": text, "metadata": {"source": str(path), "filename": path.name, "type": "markdown"}}]
