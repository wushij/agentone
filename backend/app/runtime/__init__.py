"""app/runtime — Agent Runtime（§2）：平台核心，API 层唯一入口"""

from app.runtime.runtime import AgentRuntime, get_runtime

__all__ = ["AgentRuntime", "get_runtime"]
