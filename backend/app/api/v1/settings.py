"""backend/app/api/settings.py"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.utils.response import success
from app.api.deps import require_permission
from app.models.user import User
from app.services.system.settings_store import settings_store

router = APIRouter(prefix="/api/settings", tags=["系统配置"])


class SettingsUpdateRequest(BaseModel):
    site_name: str | None = Field(default=None, alias="siteName")
    announcement: str | None = None
    default_model: str | None = Field(default=None, alias="defaultModel")
    default_temperature: float | None = Field(default=None, alias="defaultTemperature")
    max_context: int | None = Field(default=None, alias="maxContext")
    jwt_expire_minutes: int | None = Field(default=None, alias="jwtExpireMinutes")
    rate_limit_enabled: bool | None = Field(default=None, alias="rateLimitEnabled")
    rate_limit_per_minute: int | None = Field(default=None, alias="rateLimitPerMinute")
    ip_blacklist: str | None = Field(default=None, alias="ipBlacklist")
    theme: str | None = None
    color_mode: str | None = Field(default=None, alias="colorMode")

    model_config = {"populate_by_name": True}


async def _broadcast_announcement(body: str) -> None:
    try:
        from datetime import datetime

        from app.db.session import SessionLocal
        from app.models.user import User as UserModel
        from app.services.system.notify_hub import get_notify_hub

        hub = await get_notify_hub()
        db = SessionLocal()
        try:
            users = db.query(UserModel).filter(UserModel.status == 1).all()
            for u in users:
                await hub.publish(
                    u.id,
                    {
                        "type": "notification",
                        "payload": {
                            "id": f"ann_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "level": "info",
                            "title": "系统公告",
                            "body": body,
                            "action": {"label": "查看详情", "route": "/settings"},
                            "dismissible": True,
                            "timestamp": datetime.now().isoformat(),
                        },
                    },
                )
        finally:
            db.close()
    except Exception:
        pass


@router.get("/public")
def public_settings_api():
    data = settings_store.get_all()
    return success(
        {
            "siteName": data.get("siteName"),
            "theme": data.get("theme", "indigo"),
            "colorMode": data.get("colorMode", "light"),
        }
    )


@router.get("")
def get_settings_api(user: User = Depends(require_permission("config:manage"))):
    return success(settings_store.get_all())


@router.put("")
async def update_settings_api(
    body: SettingsUpdateRequest,
    user: User = Depends(require_permission("config:manage")),
):
    data = body.model_dump(by_alias=True, exclude_none=True)
    prev = settings_store.get_all()
    updated = settings_store.update(data)
    if body.announcement is not None and body.announcement != prev.get("announcement"):
        await _broadcast_announcement(body.announcement)
    return success(updated, message="保存成功")