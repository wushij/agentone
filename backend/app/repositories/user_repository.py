"""backend/app/repositories/user_repository.py"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.scalar(stmt)

    def create(
        self,
        *,
        username: str,
        password: str,
        nickname: str | None = None,
        role: str = "user",
        status: int = 1,
    ) -> User:
        user = User(
            username=username,
            password=password,
            nickname=nickname,
            role=role,
            status=status,
        )
        self.db.add(user)
        self.db.flush()
        return user
