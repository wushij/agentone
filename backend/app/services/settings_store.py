"""backend/app/services/settings_store.py"""

from __future__ import annotations

import json
from pathlib import Path

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

_DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "settings.json"


class SettingsStore:
    def __init__(self) -> None:
        self._cache: dict | None = None

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        if _DATA_FILE.exists():
            self._cache = {**DEFAULTS, **json.loads(_DATA_FILE.read_text(encoding="utf-8"))}
        else:
            self._cache = dict(DEFAULTS)
        return self._cache

    def get_all(self) -> dict:
        return self._load()

    def update(self, data: dict) -> dict:
        current = self._load()
        current.update({k: v for k, v in data.items() if v is not None})
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        _DATA_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        self._cache = current
        return current


settings_store = SettingsStore()
