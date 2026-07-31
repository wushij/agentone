"""app/runtime/executor — 执行器：FC 绑定与推理循环（§3）"""

from app.runtime.executor.tool_binding import bind_tools_if_supported, extract_tool_calls

__all__ = ["bind_tools_if_supported", "extract_tool_calls"]
