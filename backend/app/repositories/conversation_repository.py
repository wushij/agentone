"""app/repositories/conversation_repository.py — 会话表仓储"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):

    def __init__(self):
        super().__init__(Conversation)

    def get_by_user_id(
        self, db: Session, user_id: int, *, skip: int = 0, limit: int = 50
    ) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return db.scalars(stmt).all()


conversation_repository = ConversationRepository()
