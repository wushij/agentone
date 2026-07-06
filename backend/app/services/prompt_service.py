"""backend/app/services/prompt_service.py"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.utils.prompt_loader import clear_prompt_cache

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
_TYPE_MAP = {
    "system": "system",
    "planner": "planner",
    "tool": "tool",
    "summary": "summary",
}


class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def list_prompts(self) -> list[Prompt]:
        return list(self.db.scalars(select(Prompt).order_by(Prompt.name)).all())

    def get_by_name(self, name: str) -> Prompt | None:
        return self.db.scalar(select(Prompt).where(Prompt.name == name))

    def get_content(self, name: str, fallback: str = "") -> str:
        row = self.get_by_name(name)
        if row and row.enabled == 1:
            return row.content
        path = _PROMPTS_DIR / f"{name}.md"
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return fallback

    def create(self, name: str, content: str, ptype: str = "custom") -> Prompt:
        if self.get_by_name(name):
            raise ValueError("Prompt 已存在")
        row = Prompt(name=name, type=ptype, content=content, version=1, enabled=1)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        clear_prompt_cache(name)
        return row

    def update(self, name: str, content: str) -> Prompt | None:
        row = self.get_by_name(name)
        if row is None:
            return None
        
        # Save previous version to history
        from app.models.prompt_history import PromptHistory
        history = PromptHistory(
            prompt_name=row.name,
            content=row.content,
            version=row.version or 1
        )
        self.db.add(history)

        row.content = content
        row.version = (row.version or 1) + 1
        self.db.commit()
        self.db.refresh(row)
        path = _PROMPTS_DIR / f"{name}.md"
        path.write_text(content, encoding="utf-8")
        clear_prompt_cache(name)
        return row

    def list_history(self, name: str) -> list[PromptHistory]:
        from app.models.prompt_history import PromptHistory
        stmt = select(PromptHistory).where(PromptHistory.prompt_name == name).order_by(PromptHistory.version.desc())
        return list(self.db.scalars(stmt).all())

    def rollback(self, name: str, version: int) -> Prompt | None:
        from app.models.prompt_history import PromptHistory
        hist = self.db.scalar(
            select(PromptHistory).where(PromptHistory.prompt_name == name, PromptHistory.version == version)
        )
        if not hist:
            return None
        row = self.get_by_name(name)
        if not row:
            return None

        # Save current version to history before overwrite
        current_hist = PromptHistory(
            prompt_name=row.name,
            content=row.content,
            version=row.version or 1
        )
        self.db.add(current_hist)

        row.content = hist.content
        row.version = (row.version or 1) + 1
        self.db.commit()
        self.db.refresh(row)

        path = _PROMPTS_DIR / f"{name}.md"
        path.write_text(hist.content, encoding="utf-8")
        clear_prompt_cache(name)
        return row

    def set_enabled(self, name: str, enabled: bool) -> Prompt | None:
        row = self.get_by_name(name)
        if row is None:
            return None
        row.enabled = 1 if enabled else 0
        self.db.commit()
        clear_prompt_cache(name)
        return row

    def delete(self, name: str) -> bool:
        row = self.get_by_name(name)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        clear_prompt_cache(name)
        return True

    def to_dict(self, row: Prompt) -> dict:
        return {
            "name": row.name,
            "type": row.type,
            "content": row.content,
            "version": row.version,
            "enabled": row.enabled == 1,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    def seed_defaults(self) -> None:
        if self.list_prompts():
            return
        for name, ptype in _TYPE_MAP.items():
            path = _PROMPTS_DIR / f"{name}.md"
            content = path.read_text(encoding="utf-8").strip() if path.exists() else f"# {name} prompt"
            self.db.add(Prompt(name=name, type=ptype, content=content, version=1, enabled=1))
        self.db.commit()
