"""backend/app/api/settings.py"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.utils.response import success
from app.api.v1.deps import require_permission
from app.models.user import User
from app.services.system.settings_store import settings_store

router = APIRouter(prefix="/settings", tags=["系统配置"])


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
    db: Session = Depends(get_db),
):
    data = body.model_dump(by_alias=True, exclude_none=True)
    prev = dict(settings_store.get_all())
    updated = settings_store.update(data)
    if body.announcement is not None and body.announcement != prev.get("announcement"):
        await _broadcast_announcement(body.announcement)

    try:
        from app.services.system.audit_log_service import AuditLogService
        field_labels = {
            "siteName": "网站名称",
            "announcement": "系统公告",
            "defaultModel": "默认模型",
            "defaultTemperature": "温度参数",
            "maxContext": "最大上下文",
            "jwtExpireMinutes": "登录有效时长",
            "rateLimitEnabled": "限流开关",
            "rateLimitPerMinute": "每分钟频次限制",
            "ipBlacklist": "IP黑名单",
            "theme": "系统主题",
            "colorMode": "亮暗模式",
        }
        changes = []
        for k, v in data.items():
            old_v = prev.get(k)
            if old_v != v and str(old_v) != str(v):
                label = field_labels.get(k, k)
                old_str = "无" if old_v is None else str(old_v)
                new_str = "无" if v is None else str(v)
                changes.append(f"{label} [{old_str} ➔ {new_str}]")
        detail_msg = f"修改了系统配置: {', '.join(changes)}" if changes else "保存了系统配置 (无参数变更)"

        AuditLogService(db).write(
            user_id=user.id,
            module="system",
            action="update_settings",
            detail=detail_msg,
        )
    except Exception:
        pass

    return success(updated, message="保存成功")