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
from uuid import uuid4

from app.utils.logger import logger

_STREAM_KEY = "agentone:events"
_GROUP = "agentone-workers"
_MAX_DELIVERIES = 5  # 投递超过此次数仍失败→视为毒丸消息，ack 丢弃防死循环

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


async def _dispatch(fields: dict) -> bool:
    record = {
        "event_type": fields.get("event_type", ""),
        "sender": fields.get("sender", ""),
        "data": _safe_json(fields.get("data", "{}")),
        "ts": fields.get("ts", ""),
    }
    handlers = STREAM_HANDLERS or [_audit_trail]
    # 修复（§4.7）：不再静默吞 handler 异常；任一 handler 报错则返回 False（不 ack，保留 pending 重投）。
    results = await asyncio.gather(*(h(record) for h in handlers), return_exceptions=True)
    ok = True
    for r in results:
        if isinstance(r, Exception):
            ok = False
            logger.warning(f"[EventStream] handler 处理失败: {r}")
    return ok


def _safe_json(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        return raw


async def _loop() -> None:
    from app.db.redis import get_redis

    # 修复（§4.7）：consumer 名唯一，避免多实例/重启共享同一身份导致 pending 归属混乱。
    consumer = f"worker-{uuid4().hex[:8]}"
    try:
        redis = await get_redis()
        await _ensure_group(redis)
    except Exception as exc:
        logger.warning(f"[EventStream] 消费组初始化失败，reader 未启动（Redis 不可用）: {exc}")
        return

    logger.info(f"[EventStream] Redis Stream 消费组 reader 已启动（consumer={consumer}）")
    while True:
        try:
            # 修复（§4.7）：先 reclaim 其他已崩溃 consumer 遗留的 pending（崩溃重放）
            await _reclaim_pending(redis, consumer)
            resp = await redis.xreadgroup(_GROUP, consumer, {_STREAM_KEY: ">"}, count=32, block=5000)
            if not resp:
                continue
            for _stream, entries in resp:
                for entry_id, fields in entries:
                    ok = await _dispatch(fields)
                    if ok:
                        await redis.xack(_STREAM_KEY, _GROUP, entry_id)
                    # 失败则不 ack：留在 pending，由 _reclaim_pending 后续重投（超 _MAX_DELIVERIES 丢弃）
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning(f"[EventStream] 消费循环异常（2s 后重试）: {exc}")
            await asyncio.sleep(2)


async def _reclaim_pending(redis, consumer: str) -> None:
    """修复（§4.7）：用 XAUTOCLAIM 重投闲置>60s 的 pending；投递超限的毒丸消息 ack 丢弃。"""
    try:
        resp = await redis.xautoclaim(_STREAM_KEY, _GROUP, consumer, min_idle_time=60000, start_id="0-0", count=16)
        # redis-py 返回 (next_cursor, claimed_entries, [deleted])
        claimed = resp[1] if isinstance(resp, (list, tuple)) and len(resp) >= 2 else []
        for entry_id, fields in claimed or []:
            ok = await _dispatch(fields)
            if ok:
                await redis.xack(_STREAM_KEY, _GROUP, entry_id)
            else:
                # 查投递次数，超限则 ack 丢弃避免毒丸死循环
                try:
                    info = await redis.xpending_range(_STREAM_KEY, _GROUP, min=entry_id, max=entry_id, count=1)
                    delivered = int(info[0]["times_delivered"]) if info else 0
                    if delivered >= _MAX_DELIVERIES:
                        logger.error(f"[EventStream] 毒丸消息 {entry_id} 已投递 {delivered} 次，ack 丢弃")
                        await redis.xack(_STREAM_KEY, _GROUP, entry_id)
                except Exception:
                    pass
    except Exception:
        # XAUTOCLAIM 不可用（旧版 Redis）或无 pending：忽略
        pass


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
