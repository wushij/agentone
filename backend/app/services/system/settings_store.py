"""backend/app/services/settings_store.py — 统一系统配置访问门面

P0-3 双源统一：MySQL system_settings 表为唯一真相源。
- 首次加载时若 DB 为空且存在旧版 data/settings.json，自动迁移入库；
- DB 不可用（如单测 SQLite 未建表前）降级读 JSON/默认值，不阻断主链路。
"""

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
    # 多模态功能开关与模型（§多模态工具）
    "imageEnabled": True,
    "ocrEnabled": True,
    "documentEnabled": True,
    "audioEnabled": True,
    "videoEnabled": True,
    "visionModel": "",
    "sttModel": "whisper-1",
}


def _decode(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value


def _encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


class SettingsStore:
    """系统统一配置门面 (与运行状态同步)

    求值优先级:
      1. 动态配置 (MySQL system_settings，JSON 文件仅作降级)
      2. 环境变量 (config/settings.py)
      3. 静态默认值 (DEFAULTS)
    """

    def __init__(self) -> None:
        self._cache: dict | None = None

    # ---------- 内部加载 ----------

    def _load_json_file(self) -> dict:
        path = settings_json()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _load_db(self) -> dict | None:
        """从 MySQL 加载全部键值；表不存在/连接失败返回 None 触发降级。"""
        try:
            from app.db.session import SessionLocal
            from app.models.system_setting import SystemSetting

            db = SessionLocal()
            try:
                rows = db.query(SystemSetting).all()
                return {row.key: _decode(row.value) for row in rows}
            finally:
                db.close()
        except Exception:
            return None

    def _migrate_json_to_db(self) -> bool:
        """DB 为空时把旧版 JSON 配置一次性迁移入库。"""
        legacy = self._load_json_file()
        if not legacy:
            return False
        try:
            from app.db.session import SessionLocal
            from app.models.system_setting import SystemSetting

            db = SessionLocal()
            try:
                for key, value in legacy.items():
                    db.merge(SystemSetting(key=key, value=_encode(value)))
                db.commit()
                return True
            finally:
                db.close()
        except Exception:
            return False

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache

        db_values = self._load_db()
        if db_values is not None:
            if not db_values and self._migrate_json_to_db():
                db_values = self._load_db() or {}
            self._cache = {**DEFAULTS, **db_values}
        else:
            # DB 不可用：降级 JSON 文件
            self._cache = {**DEFAULTS, **self._load_json_file()}
        return self._cache

    # ---------- 对外接口（签名不变） ----------

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
        changed = {k: v for k, v in data.items() if v is not None}
        current.update(changed)

        wrote_db = False
        try:
            from app.db.session import SessionLocal
            from app.models.system_setting import SystemSetting

            db = SessionLocal()
            try:
                for key, value in changed.items():
                    db.merge(SystemSetting(key=key, value=_encode(value)))
                db.commit()
                wrote_db = True
            finally:
                db.close()
        except Exception:
            pass

        if not wrote_db:
            # DB 不可用时降级写 JSON，保证配置不丢
            try:
                path = settings_json()
                path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

        self._cache = current
        return current

    def invalidate(self) -> None:
        """外部变更后强制下次重新加载。"""
        self._cache = None


settings_store = SettingsStore()
