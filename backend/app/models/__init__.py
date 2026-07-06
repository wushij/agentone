"""Register ORM models for metadata creation."""

from app.models.audit_log import AuditLog  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.file_asset import FileAsset  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.model_config import ModelConfig  # noqa: F401
from app.models.prompt import Prompt  # noqa: F401
from app.models.prompt_history import PromptHistory  # noqa: F401
from app.models.tool_config import ToolConfig  # noqa: F401
from app.models.tool_log import ToolLog  # noqa: F401
from app.models.user import User  # noqa: F401
