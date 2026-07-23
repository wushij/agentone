"""backend/app/api/ws.py"""



from __future__ import annotations



import json



from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from sqlalchemy.orm import Session



from app.api.deps import resolve_user_from_token

from app.db.redis import get_redis

from app.db.session import SessionLocal

from app.models.conversation import Conversation

from app.services.system.notify_hub import connection_manager, get_notify_hub



router = APIRouter(prefix="/api/ws", tags=["WebSocket"])





def _validate_topics(user_id: int, db: Session, topics: list[str]) -> tuple[list[str], list[str]]:

    allowed: list[str] = []

    denied: list[str] = []

    for topic in topics:

        if topic in {"notification", "system", "task_progress"}:

            allowed.append(topic)

            continue

        if topic.startswith("agent:"):

            conv_id = topic.split(":", 1)[1]

            conv = db.get(Conversation, conv_id)

            if conv and conv.user_id == user_id:

                allowed.append(topic)

            else:

                denied.append(topic)

            continue

        if topic.startswith("task:"):

            allowed.append(topic)

            continue

        denied.append(topic)

    return allowed, denied





@router.websocket("/notify")

async def notify_websocket(

    websocket: WebSocket,

    token: str = Query(...),

):

    db: Session = SessionLocal()

    try:

        redis = await get_redis()

        user = await resolve_user_from_token(token, db, redis)

    except Exception:

        await websocket.close(code=4001)

        db.close()

        return



    await connection_manager.connect(user.id, websocket)

    try:

        while True:

            raw = await websocket.receive_text()

            try:

                message = json.loads(raw)

            except json.JSONDecodeError:

                continue



            msg_type = message.get("type")

            if msg_type == "ping":

                await websocket.send_json({"type": "pong"})

            elif msg_type == "subscribe":

                payload = message.get("payload") or {}

                topics = payload.get("topics") or []

                allowed, denied = _validate_topics(user.id, db, topics)

                if allowed:

                    connection_manager.subscribe(websocket, allowed)

                if denied:

                    await websocket.send_json(

                        {

                            "type": "error",

                            "code": "WS_SUBSCRIBE_DENIED",

                            "payload": {"topics": denied},

                        }

                    )

                else:

                    await websocket.send_json({"type": "ack", "payload": {"topics": allowed}})

            elif msg_type == "unsubscribe":

                payload = message.get("payload") or {}

                topics = payload.get("topics") or []

                connection_manager.unsubscribe(websocket, topics)

                await websocket.send_json({"type": "ack", "payload": {"topics": topics}})

    except WebSocketDisconnect:

        pass

    finally:

        connection_manager.disconnect(user.id, websocket)

        db.close()





async def init_notify_listener() -> None:

    hub = await get_notify_hub()

    await hub.start_listener()





async def shutdown_notify_listener() -> None:

    hub = await get_notify_hub()

    await hub.stop_listener()


