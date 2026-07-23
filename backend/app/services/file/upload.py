"""app/services/file/upload.py — 落盘统一走 app.storage"""

from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.storage import uploads_dir


class UploadService:
    def __init__(self, upload_dir: str | Path | None = None):
        self.upload_dir = Path(upload_dir) if upload_dir else uploads_dir()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile, user_id: str = "") -> dict[str, Any]:
        file_path = self.upload_dir / (file.filename or "unknown")
        content = await file.read()
        file_path.write_bytes(content)
        return {
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path),
        }

    async def delete_file(self, filename: str) -> bool:
        file_path = self.upload_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False
