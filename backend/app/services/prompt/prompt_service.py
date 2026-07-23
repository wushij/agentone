"""backend/app/services/prompt_service.py"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.utils.prompt_loader import clear_prompt_cache

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
_TYPE_MAP = {
    "persona": "persona",
    "system": "system",
    "planner": "planner",
    "tool": "tool",
    "summary": "summary",
    "prompt_engineer": "prompt_engineer",
}
_LEGACY_MARKERS: dict[str, tuple[str, ...]] = {
    "system": ("你是 AgentOne 企业级 AI 智能体助手",),
    "summary": ("对本轮对话进行简洁总结",),
}


class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def list_prompts(self, *, page: int = 1, size: int = 10) -> tuple[list[Prompt], int]:
        count_stmt = select(func.count()).select_from(Prompt)
        total = int(self.db.scalar(count_stmt) or 0)
        rows = list(
            self.db.scalars(
                select(Prompt).order_by(Prompt.name).offset((page - 1) * size).limit(size)
            ).all()
        )
        return rows, total

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

    def list_history(self, name: str, *, page: int = 1, size: int = 10) -> tuple[list, int]:
        from app.models.prompt_history import PromptHistory

        count_stmt = (
            select(func.count())
            .select_from(PromptHistory)
            .where(PromptHistory.prompt_name == name)
        )
        total = int(self.db.scalar(count_stmt) or 0)
        stmt = (
            select(PromptHistory)
            .where(PromptHistory.prompt_name == name)
            .order_by(PromptHistory.version.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(self.db.scalars(stmt).all()), total

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
        if name in _TYPE_MAP:
            raise ValueError("内置 Prompt 不可删除，请使用停用或文件同步")
        row = self.get_by_name(name)
        if row is None:
            return False
        if row.type != "custom":
            raise ValueError("仅自定义 Prompt 可删除")
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

    def _read_file_content(self, name: str) -> str:
        path = _PROMPTS_DIR / f"{name}.md"
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return f"# {name} prompt"

    def ensure_builtin_prompts(self, sync_files: bool = True) -> list[str]:
        """补齐内置 Prompt；若本地 .md 比库内更新则同步入库。"""
        changed: list[str] = []
        for name, ptype in _TYPE_MAP.items():
            path = _PROMPTS_DIR / f"{name}.md"
            file_content = self._read_file_content(name)
            row = self.get_by_name(name)
            if row is None:
                self.db.add(
                    Prompt(name=name, type=ptype, content=file_content, version=1, enabled=1)
                )
                changed.append(name)
                continue
            if not sync_files or not path.exists():
                continue
            stale = row.content.strip() != file_content and (
                name in _LEGACY_MARKERS
                and any(marker in row.content for marker in _LEGACY_MARKERS[name])
            )
            content_outdated = row.content.strip() != file_content
            if stale or content_outdated:
                row.content = file_content
                row.version = (row.version or 1) + 1
                changed.append(name)
        if changed:
            self.db.commit()
            for name in changed:
                clear_prompt_cache(name)
        return changed

    def seed_defaults(self) -> None:
        if not self.db.scalar(select(func.count()).select_from(Prompt)):
            for name, ptype in _TYPE_MAP.items():
                content = self._read_file_content(name)
                self.db.add(Prompt(name=name, type=ptype, content=content, version=1, enabled=1))
            self.db.commit()
        self.ensure_builtin_prompts(sync_files=True)
