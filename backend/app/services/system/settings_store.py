"""backend/app/services/settings_store.py — 统一系统配置访问门面"""

from __future__ import annotations

import json
from typing import Any

from app.config.settings import settings
from app.storage import settings_json

DEFAULTS = {
    "siteName": "AgentOne",
    "announcement": "欢迎使用 AgentOne 企业级 AI 智能体平台。",
    "defaultModel": "deepseek-chat",
    "defaultTemperature": 0.7,
    "maxContext": 8192,
    "jwtExpireMinutes": 1440,
    "rateLimitEnabled": True,
    "rateLimitPerMinute": 120,
    "theme": "indigo",
    "colorMode": "light",
}


class SettingsStore:
    """系统统一配置门面 (与运行状态同步)

    求值优先级:
      1. 动态配置 (settings_store 运行时 JSON/DB)
      2. 环境变量 (config/settings.py)
      3. 静态默认值 (DEFAULTS)
    """

    def __init__(self) -> None:
        self._cache: dict | None = None

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        path = settings_json()
        if path.exists():
            try:
                self._cache = {**DEFAULTS, **json.loads(path.read_text(encoding="utf-8"))}
            except Exception:
                self._cache = dict(DEFAULTS)
        else:
            self._cache = dict(DEFAULTS)
        return self._cache

    def get(self, key: str, default: Any = None) -> Any:
        """统一键值解析器，实现动态/静态优先求值。"""
        store = self._load()
        if key in store:
            return store[key]
        # 兼容蛇形/驼峰访问 config/settings.py
        env_val = getattr(settings, key.upper(), None)
        if env_val is not None:
            return env_val
        return DEFAULTS.get(key, default)

    def get_all(self) -> dict:
        return self._load()

    def update(self, data: dict) -> dict:
        current = self._load()
        current.update({k: v for k, v in data.items() if v is not None})
        path = settings_json()
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        self._cache = current
        return current


settings_store = SettingsStore()
