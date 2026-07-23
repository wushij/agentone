"""app/repositories/knowledge_repository.py — 知识库/文件资产仓储"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file_asset import FileAsset
from app.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository[FileAsset]):

    def __init__(self):
        super().__init__(FileAsset)

    def get_by_kb_id(self, db: Session, kb_id: str) -> Sequence[FileAsset]:
        stmt = select(FileAsset).where(FileAsset.kb_id == kb_id)
        return db.scalars(stmt).all()


knowledge_repository = KnowledgeRepository()
