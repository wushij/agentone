"""app/repositories/user_repository.py — 用户表仓储"""

from typing import Any, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, db: Session | None = None):
        super().__init__(User, db)

    def get_by_username(
        self, db_or_username: Any, username: str | None = None
    ) -> User | None:
        if isinstance(db_or_username, Session):
            session = db_or_username
            name = username
        else:
            session = self.db
            name = db_or_username
        if not session or not name:
            return None
        stmt = select(User).where(User.username == name)
        return session.scalars(stmt).first()

    def get_by_id(self, db_or_id: Any, user_id: int | None = None) -> User | None:
        if isinstance(db_or_id, Session):
            session = db_or_id
            target_id = user_id
        else:
            session = self.db
            target_id = db_or_id
        if not session or not target_id:
            return None
        return session.get(User, target_id)

    def get_all(self, db: Session | None = None, *, skip: int = 0, limit: int = 100) -> Sequence[User]:
        session = db or self.db
        if not session:
            raise ValueError("Session is required")
        stmt = select(User).offset(skip).limit(limit)
        return session.scalars(stmt).all()


user_repository = UserRepository()
