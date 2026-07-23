"""app/events/listener.py — 全局事件监听器助手"""

from app.events.bus import HandlerFunc, event_bus


def on_event(event_type: str):
    """事件监听器装饰器。"""

    def decorator(func: HandlerFunc):
        event_bus.subscribe(event_type, func)
        return func

    return decorator
