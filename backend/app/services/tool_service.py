"""backend/app/services/tool_service.py"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tool_config import ToolConfig
from app.tools.registry import get_tool, list_builtin_tools


class ToolService:
    def __init__(self, db: Session):
        self.db = db

    def list_configs(self) -> list[ToolConfig]:
        return list(self.db.scalars(select(ToolConfig).order_by(ToolConfig.name)).all())

    def get_config(self, name: str) -> ToolConfig | None:
        return self.db.get(ToolConfig, name)

    def is_enabled(self, name: str) -> bool:
        cfg = self.get_config(name)
        if cfg is None:
            return True
        return cfg.enabled == 1

    def list_tools(self) -> list[dict]:
        configs = {c.name: c for c in self.list_configs()}
        items: list[dict] = []
        for builtin in list_builtin_tools():
            cfg = configs.get(builtin.name)
            items.append(
                {
                    "name": builtin.name,
                    "description": builtin.description,
                    "type": cfg.tool_type if cfg else "builtin",
                    "status": "enabled" if (cfg.enabled if cfg else 1) == 1 else "disabled",
                }
            )
        for name, cfg in configs.items():
            if name not in {b.name for b in list_builtin_tools()}:
                items.append(
                    {
                        "name": cfg.name,
                        "description": cfg.description,
                        "type": cfg.tool_type,
                        "status": "enabled" if cfg.enabled == 1 else "disabled",
                    }
                )
        return items

    def set_enabled(self, name: str, enabled: bool) -> ToolConfig:
        cfg = self.get_config(name)
        tool = get_tool(name)
        description = tool.description if tool else ""
        if cfg is None:
            cfg = ToolConfig(name=name, description=description, tool_type="builtin", enabled=1 if enabled else 0)
            self.db.add(cfg)
        else:
            cfg.enabled = 1 if enabled else 0
        self.db.commit()
        self.db.refresh(cfg)
        return cfg

    def update(self, name: str, data: dict) -> ToolConfig | None:
        cfg = self.get_config(name)
        if cfg is None:
            tool = get_tool(name)
            if tool is None:
                return None
            cfg = ToolConfig(name=name, description=tool.description, tool_type="builtin")
            self.db.add(cfg)
        if "description" in data and data["description"] is not None:
            cfg.description = data["description"]
        if "status" in data and data["status"] is not None:
            cfg.enabled = 0 if data["status"] == "disabled" else 1
        self.db.commit()
        self.db.refresh(cfg)
        return cfg

    def seed_defaults(self) -> None:
        if self.list_configs():
            return
        for tool in list_builtin_tools():
            self.db.add(
                ToolConfig(
                    name=tool.name,
                    description=tool.description,
                    tool_type="builtin",
                    enabled=1,
                )
            )
        self.db.commit()
