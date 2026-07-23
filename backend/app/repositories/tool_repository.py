"""app/repositories/tool_repository.py — 工具配置仓储"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tool_config import ToolConfig
from app.repositories.base import BaseRepository


class ToolRepository(BaseRepository[ToolConfig]):

    def __init__(self):
        super().__init__(ToolConfig)

    def get_by_name(self, db: Session, name: str) -> ToolConfig | None:
        stmt = select(ToolConfig).where(ToolConfig.name == name)
        return db.scalars(stmt).first()


tool_repository = ToolRepository()
