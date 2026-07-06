"""backend/app/services/file_service.py"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.file_asset import FileAsset, new_file_id

_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
_ALLOWED_EXT = {".pdf", ".doc", ".docx", ".txt", ".md", ".markdown", ".xlsx", ".xls"}


class FileService:
    def __init__(self, db: Session):
        self.db = db
        _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def list_files(self, user_id: int, *, keyword: str = "") -> list[FileAsset]:
        stmt = select(FileAsset).where(FileAsset.user_id == user_id)
        if keyword:
            stmt = stmt.where(FileAsset.original_name.like(f"%{keyword}%"))
        return list(self.db.scalars(stmt.order_by(desc(FileAsset.created_at))).all())

    def get_file(self, user_id: int, file_id: str) -> FileAsset | None:
        row = self.db.get(FileAsset, file_id)
        if row is None or row.user_id != user_id:
            return None
        return row

    async def upload(self, user_id: int, file: UploadFile, category: str = "general") -> FileAsset:
        original = file.filename or "unnamed"
        ext = Path(original).suffix.lower()
        if ext not in _ALLOWED_EXT:
            raise ValueError(f"不支持的文件格式: {ext or '未知'}")
        file_id = new_file_id()
        stored_name = f"{file_id}{ext}"
        dest = _UPLOAD_DIR / stored_name
        content = await file.read()
        dest.write_bytes(content)
        row = FileAsset(
            id=file_id,
            user_id=user_id,
            filename=stored_name,
            original_name=original,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            category=category,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def resolve_path(self, row: FileAsset) -> Path:
        return _UPLOAD_DIR / row.filename

    def delete(self, user_id: int, file_id: str) -> bool:
        row = self.get_file(user_id, file_id)
        if row is None:
            return False
        path = self.resolve_path(row)
        if path.exists():
            path.unlink()
        self.db.delete(row)
        self.db.commit()
        return True

    def to_dict(self, row: FileAsset) -> dict:
        def fmt_size(n: int) -> str:
            if n < 1024:
                return f"{n} B"
            if n < 1024 * 1024:
                return f"{n / 1024:.1f} KB"
            return f"{n / 1024 / 1024:.1f} MB"

        return {
            "id": row.id,
            "name": row.original_name,
            "type": Path(row.original_name).suffix.replace(".", "").upper() or "FILE",
            "size": fmt_size(row.size_bytes),
            "sizeBytes": row.size_bytes,
            "category": row.category,
            "mimeType": row.mime_type,
            "time": row.created_at.strftime("%Y-%m-%d %H:%M"),
            "createdAt": row.created_at.isoformat(),
        }
