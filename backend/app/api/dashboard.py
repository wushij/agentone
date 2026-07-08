"""backend/app/api/dashboard.py"""



from __future__ import annotations



from datetime import datetime, timedelta



from fastapi import APIRouter, Depends

from sqlalchemy import func, select

from sqlalchemy.orm import Session



from app.common.response import success

from app.core.config import get_settings

from app.core.deps import get_current_user

from app.db.session import get_db

from app.models.conversation import Conversation

from app.models.message import Message

from app.models.tool_log import ToolLog

from app.models.user import User

from app.services.conversation_service import ConversationService
from app.services.model_service import ModelService
from app.services.settings_store import settings_store
from app.services.user_stats_service import get_deleted_tokens

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])





@router.get("/stats")

def dashboard_stats(

    user: User = Depends(get_current_user),

    db: Session = Depends(get_db),

):

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    conv_service = ConversationService(db)

    settings = get_settings()

    store = settings_store.get_all()



    today_conversations = db.scalar(

        select(func.count(Conversation.id)).where(

            Conversation.user_id == user.id,

            Conversation.created_at >= today_start,

        )

    ) or 0



    total_tokens = db.scalar(
        select(func.coalesce(func.sum(Message.tokens), 0))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == user.id)
    ) or 0
    total_tokens += get_deleted_tokens(user.id)



    tool_calls = db.scalar(

        select(func.count(ToolLog.id)).where(ToolLog.user_id == user.id)

    ) or 0



    weekly: list[dict] = []

    for offset in range(6, -1, -1):

        day = today_start - timedelta(days=offset)

        next_day = day + timedelta(days=1)

        count = db.scalar(

            select(func.count(Conversation.id)).where(

                Conversation.user_id == user.id,

                Conversation.created_at >= day,

                Conversation.created_at < next_day,

            )

        ) or 0

        weekly.append({"date": day.strftime("%m-%d"), "count": int(count)})



    recent = conv_service.list_conversations(user.id, page=1, size=5).records
    announcement = store.get("announcement", "")

    model_service = ModelService(db)
    active_model = model_service.get_default()

    if active_model:
        model_name = active_model.model_name
        model_status = "online"
    else:
        if settings.LLM_PROVIDER == "deepseek" and settings.DEEPSEEK_API_KEY:
            model_name = settings.DEEPSEEK_MODEL
            model_status = "online"
        elif settings.LLM_PROVIDER == "mock":
            model_name = "mock-chat"
            model_status = "online"
        else:
            model_name = "未配置模型"
            model_status = "offline"

    return success(
        {
            "todayConversations": today_conversations,
            "totalTokens": int(total_tokens),
            "toolCalls": int(tool_calls),
            "modelStatus": model_status,
            "modelName": model_name,
            "recentConversations": [item.model_dump(by_alias=True) for item in recent],
            "weeklyConversations": weekly,
            "tokenUsagePercent": min(100, int(total_tokens / 10000 * 100)) if total_tokens else 0,
            "announcements": [
                {
                    "id": "ann_system",
                    "title": "系统公告",
                    "body": announcement,
                    "timestamp": datetime.now().isoformat(),
                }
            ]
            if announcement
            else [],
        }
    )


