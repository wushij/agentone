"""backend/app/tools/registry.py"""

from __future__ import annotations

from app.tools.base import BaseTool
from app.tools.compute.calculator import CalculatorTool
from app.tools.compute.python_executor import PythonExecutorTool
from app.tools.data.chart import ChartTool
from app.tools.database.database import DatabaseTool
from app.tools.file.file import FileTool
from app.tools.multimodal.audio_tool import AudioTool
from app.tools.multimodal.document_tool import DocumentTool
from app.tools.multimodal.image_tool import ImageTool
from app.tools.multimodal.ocr_tool import OCRTool
from app.tools.multimodal.video_tool import VideoTool
from app.tools.network.http_request import HttpRequestTool
from app.tools.network.search import SearchTool

_TOOLS: dict[str, BaseTool] = {
    CalculatorTool.name: CalculatorTool(),
    SearchTool.name: SearchTool(),
    FileTool.name: FileTool(),
    DatabaseTool.name: DatabaseTool(),
    PythonExecutorTool.name: PythonExecutorTool(),
    ChartTool.name: ChartTool(),
    HttpRequestTool.name: HttpRequestTool(),
    ImageTool.name: ImageTool(),
    OCRTool.name: OCRTool(),
    DocumentTool.name: DocumentTool(),
    AudioTool.name: AudioTool(),
    VideoTool.name: VideoTool(),
}


def is_tool_enabled(name: str) -> bool:
    try:
        from app.db.session import SessionLocal
        from app.services.tool.tool_service import ToolService

        db = SessionLocal()
        try:
            return ToolService(db).is_enabled(name)
        finally:
            db.close()
    except Exception:
        return True


def get_tool(name: str) -> BaseTool | None:
    return _TOOLS.get(name)


def list_tools() -> list[str]:
    return list(_TOOLS.keys())


def list_builtin_tools() -> list[BaseTool]:
    return list(_TOOLS.values())


def list_tool_infos() -> list[dict[str, str]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "status": "enabled" if is_tool_enabled(tool.name) else "disabled",
        }
        for tool in _TOOLS.values()
    ]


class ToolRegistry:

    def get(self, name: str) -> BaseTool | None:
        return get_tool(name)

    def is_enabled(self, name: str) -> bool:
        return is_tool_enabled(name)

    def list_all(self) -> list[BaseTool]:
        return list_builtin_tools()


tool_registry = ToolRegistry()
