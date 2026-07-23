"""app/utils/file_utils.py"""

from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".json", ".csv", ".xlsx"}


def is_allowed_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_size(filepath: Path) -> int:
    return filepath.stat().st_size if filepath.exists() else 0


def safe_filename(filename: str) -> str:
    return "".join(c for c in filename if c.isalnum() or c in "._- ").strip()