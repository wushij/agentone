"""app/schemas/settings.py — 系统配置 Pydantic Schema"""

from pydantic import BaseModel


class SystemSettingsUpdate(BaseModel):
    site_title: str | None = None
    default_model: str | None = None
    enable_registration: bool | None = None
