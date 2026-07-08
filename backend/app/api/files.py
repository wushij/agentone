"""backend/app/api/files.py"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.common.pagination import clamp_page, page_result
from app.common.response import success
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["文件中心"])


@router.get("")
def list_files(
    keyword: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page, size = clamp_page(page, size)
    svc = FileService(db)
    rows, total = svc.list_files(user.id, keyword=keyword, page=page, size=size)
    return success(page_result([svc.to_dict(r) for r in rows], total))


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Query(default="general"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FileService(db)
    row = await svc.upload(user.id, file, category=category)
    AuditLogService(db).write(
        user_id=user.id,
        module="file",
        action="upload",
        detail=row.original_name,
    )
    return success(svc.to_dict(row), message="上传成功")


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FileService(db)
    row = svc.get_file(user.id, file_id)
    if row is None:
        raise ValueError("文件不存在")
    path = svc.resolve_path(row)
    if not path.exists():
        raise ValueError("文件已丢失")
    return FileResponse(path, filename=row.original_name, media_type=row.mime_type)


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FileService(db)
    row = svc.get_file(user.id, file_id)
    if row is None:
        raise ValueError("文件不存在")
    original_name = row.original_name
    if not svc.delete(user.id, file_id):
        raise ValueError("删除失败")
    AuditLogService(db).write(user_id=user.id, module="file", action="delete", detail=original_name)
    return success(None, message="已删除")

