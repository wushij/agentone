"""app/runtime/router — Model Router（§9.1）"""

from app.runtime.router.model_router import (
    ainvoke_with_fallback,
    create_model_for_role,
)

__all__ = ["ainvoke_with_fallback", "create_model_for_role"]
