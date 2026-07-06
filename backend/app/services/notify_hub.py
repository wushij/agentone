"""backend/app/services/notify_hub.py"""



from __future__ import annotations



import asyncio

import json

from datetime import datetime, timezone

from uuid import uuid4



from fastapi import WebSocket

from redis.asyncio import Redis



from app.db.redis import get_redis



_DEFAULT_TOPICS = frozenset({"notification", "system"})





class ConnectionManager:

    def __init__(self) -> None:

        self._connections: dict[int, list[WebSocket]] = {}

        self._subscriptions: dict[WebSocket, set[str]] = {}



    async def connect(self, user_id: int, websocket: WebSocket, *, kick_existing: bool = True) -> None:

        await websocket.accept()

        self._subscriptions[websocket] = set(_DEFAULT_TOPICS)



        if kick_existing:

            for old_ws in list(self._connections.get(user_id, [])):

                try:

                    await old_ws.send_json({"type": "kick", "reason": "new_session"})

                    await old_ws.close(code=4001)

                except Exception:

                    pass

                self._subscriptions.pop(old_ws, None)

            self._connections[user_id] = [websocket]

            return



        self._connections.setdefault(user_id, []).append(websocket)



    def disconnect(self, user_id: int, websocket: WebSocket) -> None:

        self._subscriptions.pop(websocket, None)

        connections = self._connections.get(user_id, [])

        if websocket in connections:

            connections.remove(websocket)

        if not connections:

            self._connections.pop(user_id, None)

        else:

            self._connections[user_id] = connections



    def subscribe(self, websocket: WebSocket, topics: list[str]) -> None:

        subs = self._subscriptions.setdefault(websocket, set(_DEFAULT_TOPICS))

        subs.update(topics)



    def unsubscribe(self, websocket: WebSocket, topics: list[str]) -> None:

        subs = self._subscriptions.get(websocket)

        if subs:

            subs.difference_update(topics)



    @staticmethod

    def topic_for_message(message: dict) -> str | None:

        msg_type = message.get("type")

        payload = message.get("payload") or {}

        if msg_type == "agent_status":

            conv_id = payload.get("conversationId")

            return f"agent:{conv_id}" if conv_id else None

        if msg_type in _DEFAULT_TOPICS:

            return msg_type

        if msg_type == "task_progress":

            task_id = payload.get("taskId")

            return f"task:{task_id}" if task_id else "task_progress"

        return None



    async def send_to_user(self, user_id: int, message: dict) -> None:

        topic = self.topic_for_message(message)

        for websocket in list(self._connections.get(user_id, [])):

            subs = self._subscriptions.get(websocket, _DEFAULT_TOPICS)

            if topic is None or topic in subs:

                try:

                    await websocket.send_json(message)

                except Exception:

                    self.disconnect(user_id, websocket)





connection_manager = ConnectionManager()





class NotifyHub:

    def __init__(self, redis: Redis):

        self.redis = redis

        self.manager = connection_manager

        self._listener_task: asyncio.Task | None = None

        self._pubsub = None



    def _channel(self, user_id: int) -> str:

        return f"channel:notify:{user_id}"



    def _envelope(self, message: dict) -> dict:

        envelope = dict(message)

        envelope.setdefault("id", f"notif_{uuid4().hex[:12]}")

        envelope.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        envelope.setdefault("type", "notification")

        return envelope



    async def publish(self, user_id: int, message: dict) -> None:

        envelope = self._envelope(message)

        await self.manager.send_to_user(user_id, envelope)

        await self.redis.publish(self._channel(user_id), json.dumps(envelope))



    async def start_listener(self) -> None:

        if self._listener_task is not None:

            return

        self._pubsub = self.redis.pubsub()

        await self._pubsub.psubscribe("channel:notify:*")

        self._listener_task = asyncio.create_task(self._listen())



    async def stop_listener(self) -> None:

        if self._listener_task is not None:

            self._listener_task.cancel()

            try:

                await self._listener_task

            except asyncio.CancelledError:

                pass

            self._listener_task = None

        if self._pubsub is not None:

            await self._pubsub.punsubscribe("channel:notify:*")

            await self._pubsub.aclose()

            self._pubsub = None



    async def _listen(self) -> None:

        assert self._pubsub is not None

        async for raw in self._pubsub.listen():

            if raw.get("type") != "pmessage":

                continue

            channel = raw.get("channel")

            data = raw.get("data")

            if not channel or not data:

                continue

            try:

                channel_name = channel.decode() if isinstance(channel, bytes) else str(channel)

                user_id = int(channel_name.rsplit(":", 1)[-1])

                payload = json.loads(data)

                if isinstance(payload, str):

                    payload = json.loads(payload)

                await self.manager.send_to_user(user_id, payload)

            except Exception:

                continue





_notify_hub: NotifyHub | None = None





async def get_notify_hub() -> NotifyHub:

    global _notify_hub

    if _notify_hub is None:

        redis = await get_redis()

        _notify_hub = NotifyHub(redis)

    return _notify_hub


