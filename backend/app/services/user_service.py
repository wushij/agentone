"""backend/app/services/user_service.py"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreateRequest, UserItem, UserUpdateRequest


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def list_users(
        self,
        *,
        page: int = 1,
        size: int = 10,
        keyword: str = "",
    ) -> tuple[list[UserItem], int]:
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)
        if keyword.strip():
            kw = f"%{keyword.strip()}%"
            flt = or_(User.username.like(kw), User.nickname.like(kw))
            stmt = stmt.where(flt)
            count_stmt = count_stmt.where(flt)
        total = int(self.db.scalar(count_stmt) or 0)
        rows = list(
            self.db.scalars(
                stmt.order_by(User.id.asc()).offset((page - 1) * size).limit(size)
            ).all()
        )
        return [self._to_item(u) for u in rows], total

    def create_user(self, request: UserCreateRequest, *, actor_role: str) -> UserItem:
        if self.users.get_by_username(request.username.strip()):
            raise ValueError("用户名已存在")
        role = self._normalize_role(request.role, actor_role)
        user = self.users.create(
            username=request.username.strip(),
            password=hash_password(request.password),
            nickname=request.nickname or request.username.strip(),
            role=role,
            status=1,
        )
        self.db.commit()
        self.db.refresh(user)
        return self._to_item(user)

    def update_user(self, user_id: int, request: UserUpdateRequest, *, actor_role: str) -> UserItem:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise ValueError("用户不存在")
        if request.nickname is not None:
            user.nickname = request.nickname
        if request.role is not None:
            user.role = self._normalize_role(request.role, actor_role)
        if request.status is not None:
            user.status = 1 if request.status == 1 else 0
        self.db.commit()
        self.db.refresh(user)
        return self._to_item(user)

    def delete_user(self, user_id: int, *, actor_id: int) -> None:
        if user_id == actor_id:
            raise ValueError("不能删除当前登录账号")
        user = self.users.get_by_id(user_id)
        if user is None:
            raise ValueError("用户不存在")
        if user.role == "super_admin":
            raise ValueError("不能删除超级管理员")
        self.db.delete(user)
        self.db.commit()

    def register(self, username: str, password: str, nickname: str | None = None) -> UserItem:
        name = username.strip()
        if self.users.get_by_username(name):
            raise ValueError("用户名已存在")
        user = self.users.create(
            username=name,
            password=hash_password(password),
            nickname=nickname or name,
            role="user",
            status=1,
        )
        self.db.commit()
        self.db.refresh(user)
        return self._to_item(user)

    def _normalize_role(self, role: str, actor_role: str) -> str:
        allowed = {"user", "admin"}
        if actor_role == "super_admin":
            allowed.add("super_admin")
        if role not in allowed:
            raise ValueError("无效的角色")
        return role

    def _to_item(self, user: User) -> UserItem:
        return UserItem(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar=user.avatar,
            role=user.role,
            status=user.status,
            createdAt=user.created_at,
            lastLoginAt=user.last_login_at,
        )
