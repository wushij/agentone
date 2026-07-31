"""app/memory/scheduler.py — 记忆遗忘定时调度（§7.2）

轻量 asyncio 后台循环：按固定间隔触发 PersistentMemoryService.decay()
（低 importance + 长期未访问 → 衰减，衰减至阈值以下删除，置顶免疫）。
应用启动时 start_memory_decay()，关闭时 stop_memory_decay()。
"""

from __future__ import annotations

import asyncio

from app.utils.logger import logger

# 默认每 6 小时跑一次遗忘（可由 settings_store.memoryDecayIntervalHours 覆盖）
_DEFAULT_INTERVAL_H = 6

_task: asyncio.Task | None = None


def _interval_seconds() -> int:
    try:
        from app.services.system.settings_store import settings_store

        hours = float(settings_store.get("memoryDecayIntervalHours", _DEFAULT_INTERVAL_H) or _DEFAULT_INTERVAL_H)
        return max(300, int(hours * 3600))
    except Exception:
        return _DEFAULT_INTERVAL_H * 3600


async def _loop() -> None:
    from app.memory.persistent import get_persistent_memory

    # 启动后先等一个间隔，避免与冷启动争抢
    while True:
        try:
            await asyncio.sleep(_interval_seconds())
            result = get_persistent_memory().decay()
            if result.get("decayed") or result.get("removed"):
                logger.info(f"[MemoryDecay] 衰减 {result['decayed']} 条，清理 {result['removed']} 条")
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning(f"[MemoryDecay] 定时遗忘失败（下轮重试）: {exc}")


def start_memory_decay() -> None:
    global _task
    if _task is not None:
        return
    try:
        _task = asyncio.get_running_loop().create_task(_loop())
        logger.info("[MemoryDecay] 遗忘定时任务已启动")
    except RuntimeError:
        _task = None


async def stop_memory_decay() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
