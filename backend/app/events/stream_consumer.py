"""app/events/stream_consumer.py — Redis Stream 消费组 reader（§11）

EventBus 已把领域事件镜像进 Redis Stream（agentone:events）。本模块提供
消费组 reader：XREADGROUP 拉取 + ack + 崩溃重放（pending 重投），实现跨进程消费。

默认注册一个审计留痕 handler（把事件写日志，作为可追溯的事件流）；
其他跨进程消费方（Evaluator 在线抽检、Webhook 出站）后续在 STREAM_HANDLERS 扩展。
消费组独立于进程内 EventBus 分发，不会与本进程 handler 重复处理。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

from app.utils.logger import logger

_STREAM_KEY = "agentone:events"
_GROUP = "agentone-workers"

StreamHandler = Callable[[dict], Awaitable[None]]
STREAM_HANDLERS: list[StreamHandler] = []

_task: asyncio.Task | None = None


async def _audit_trail(record: dict) -> None:
    """默认消费方：事件流留痕（DEBUG 级，便于排障与重放核对）。"""
    logger.debug(f"[EventStream] {record.get('event_type')} <- {record.get('sender')} :: {record.get('data')}")


async def _ensure_group(redis) -> None:
    try:
        await redis.xgroup_create(_STREAM_KEY, _GROUP, id="0", mkstream=True)
    except Exception as exc:
        # BUSYGROUP: 组已存在，忽略
        if "BUSYGROUP" not in str(exc):
            raise


async def _dispatch(fields: dict) -> None:
    record = {
        "event_type": fields.get("event_type", ""),
        "sender": fields.get("sender", ""),
        "data": _safe_json(fields.get("data", "{}")),
        "ts": fields.get("ts", ""),
    }
    handlers = STREAM_HANDLERS or [_audit_trail]
    await asyncio.gather(*(h(record) for h in handlers), return_exceptions=True)


def _safe_json(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        return raw


async def _loop() -> None:
    from app.db.redis import get_redis

    consumer = "worker-1"
    try:
        redis = await get_redis()
        await _ensure_group(redis)
    except Exception as exc:
        logger.warning(f"[EventStream] 消费组初始化失败，reader 未启动（Redis 不可用）: {exc}")
        return

    logger.info("[EventStream] Redis Stream 消费组 reader 已启动")
    while True:
        try:
            resp = await redis.xreadgroup(_GROUP, consumer, {_STREAM_KEY: ">"}, count=32, block=5000)
            if not resp:
                continue
            for _stream, entries in resp:
                for entry_id, fields in entries:
                    try:
                        await _dispatch(fields)
                    finally:
                        await redis.xack(_STREAM_KEY, _GROUP, entry_id)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning(f"[EventStream] 消费循环异常（2s 后重试）: {exc}")
            await asyncio.sleep(2)


def start_stream_consumer() -> None:
    global _task
    if _task is not None:
        return
    try:
        _task = asyncio.get_running_loop().create_task(_loop())
    except RuntimeError:
        _task = None


async def stop_stream_consumer() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
