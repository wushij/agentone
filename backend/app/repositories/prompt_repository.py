"""app/repositories/prompt_repository.py — 提示词仓储"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.repositories.base import BaseRepository


class PromptRepository(BaseRepository[Prompt]):

    def __init__(self):
        super().__init__(Prompt)

    def get_by_name(self, db: Session, name: str) -> Prompt | None:
        stmt = select(Prompt).where(Prompt.name == name)
        return db.scalars(stmt).first()


prompt_repository = PromptRepository()
