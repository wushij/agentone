"""app/tools/multimodal/video_tool.py — 视频关键帧分析工具

需要 ffmpeg（可选依赖）：抽取关键帧 → 视觉模型识别帧画面/OCR。
未安装 ffmpeg 时优雅降级并提示，不影响其它功能。
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class VideoArgs(BaseModel):
    query: str = Field(default="", description="视频文件名关键词；留空则取最近上传的视频")
    question: str = Field(default="请描述这段视频关键帧的画面内容", description="对视频画面的提问")


def _extract_keyframe(video_path: Path) -> Path | None:
    """用 ffmpeg 抽取一帧到 temp 目录；无 ffmpeg 或失败返回 None。"""
    if shutil.which("ffmpeg") is None:
        return None
    import subprocess
    import uuid

    from app.storage import temp_dir

    out = temp_dir() / f"frame_{uuid.uuid4().hex[:8]}.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "00:00:01", "-i", str(video_path), "-frames:v", "1", str(out)],
            capture_output=True, timeout=30,
        )
        return out if out.exists() else None
    except Exception:
        return None


class VideoTool(BaseTool):
    name = "video_analyze"
    description = "分析用户上传的视频（抽取关键帧并识别画面）。用户要求看视频内容、识别视频画面时使用。"
    args_schema = VideoArgs
    timeout_s = 120.0

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()

        from app.services.multimodal import is_feature_enabled, resolve_user_file, vision_chat
        from app.services.multimodal.helpers import VIDEO_EXTS

        if not is_feature_enabled("videoEnabled"):
            return ToolResult(output="", duration_ms=0, error="视频解析功能已被管理员关闭")

        query = str(kwargs.get("query") or "").strip()
        question = str(kwargs.get("question") or "请描述这段视频关键帧的画面内容").strip()
        target, path, hint = resolve_user_file(kwargs.get("_user_id"), query, exts=VIDEO_EXTS)
        if target is None or path is None:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=hint)

        frame = _extract_keyframe(Path(path))
        if frame is None:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="视频分析需要 ffmpeg（可选依赖）。请在服务器安装 ffmpeg 后重试。",
            )
        try:
            answer = await vision_chat(frame, question)
        except Exception as exc:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=str(exc))
        finally:
            try:
                frame.unlink(missing_ok=True)
            except Exception:
                pass

        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(output=f"{hint}（关键帧识别）\n\n{answer}", duration_ms=duration_ms)
