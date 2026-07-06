"""backend/app/api/users.py"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import success
from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.audit_log_service import AuditLogService
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["用户管理"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("")
def list_users(
    user: User = Depends(require_permission("user:manage")),
    service: UserService = Depends(get_user_service),
):
    return success([u.model_dump(by_alias=True) for u in service.list_users()])


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
