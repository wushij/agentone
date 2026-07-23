"""app/repositories/message_repository.py — 消息表仓储"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):

    def __init__(self):
        super().__init__(Message)

    def get_by_conversation_id(
        self, db: Session, conversation_id: int, *, limit: int = 100
    ) -> Sequence[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
            .limit(limit)
        )
        return db.scalars(stmt).all()


message_repository = MessageRepository()
