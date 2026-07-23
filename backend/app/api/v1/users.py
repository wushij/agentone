"""backend/app/api/users.py"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.utils.pagination import clamp_page, page_result
from app.utils.response import success
from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.system.audit_log_service import AuditLogService
from app.services.user.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["用户管理"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("")
def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    keyword: str = Query(default=""),
    user: User = Depends(require_permission("user:manage")),
    service: UserService = Depends(get_user_service),
):
    page, size = clamp_page(page, size)
    rows, total = service.list_users(page=page, size=size, keyword=keyword)
    records = [u.model_dump(by_alias=True) for u in rows]
    return success(page_result(records, total))


@router.post("")
def create_user(
    body: UserCreateRequest,
    user: User = Depends(require_permission("user:manage")),
    service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
):
    item = service.create_user(body, actor_role=user.role)
    AuditLogService(db).write(
        user_id=user.id,
        module="user",
        action="create",
        detail=f"username={body.username}",
    )
    return success(item.model_dump(by_alias=True), message="创建成功")


@router.put("/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdateRequest,
    user: User = Depends(require_permission("user:manage")),
    service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
):
    item = service.update_user(user_id, body, actor_role=user.role)
    AuditLogService(db).write(
        user_id=user.id,
        module="user",
        action="update",
        detail=f"target={user_id}",
    )
    return success(item.model_dump(by_alias=True), message="更新成功")


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    user: User = Depends(require_permission("user:manage")),
    service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
):
    service.delete_user(user_id, actor_id=user.id)
    AuditLogService(db).write(
        user_id=user.id,
        module="user",
        action="delete",
        detail=f"target={user_id}",
    )
    return success(None, message="已删除")