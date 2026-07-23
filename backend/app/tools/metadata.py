"""app/tools/metadata.py — Agent 工具元数据规范"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolMetadata:
    """工具定义元数据，供 Agent 自动发现与 LLM Function Calling Schema 生成。"""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    permission: str = "user"  # "public", "user", "admin"
    timeout: int = 30
    version: str = "1.0.0"

    def to_openai_function_schema(self) -> dict[str, Any]:
        """导出为 OpenAI / DeepSeek Function Call JSON Schema 结构。"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters.get("properties", {}),
                "required": self.parameters.get("required", []),
            },
        }
