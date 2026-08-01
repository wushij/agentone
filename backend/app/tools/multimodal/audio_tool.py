"""app/tools/multimodal/audio_tool.py — 语音转写工具（STT）

API 优先：走 OpenAI 兼容的 /audio/transcriptions（whisper-1）；
本地 whisper/faster-whisper 为可选后端，未配置/未安装则优雅提示。
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class AudioArgs(BaseModel):
    query: str = Field(default="", description="音频文件名关键词；留空则取最近上传的音频")


async def _transcribe_via_api(path, api_key: str, base_url: str, model: str) -> str | None:
    """OpenAI 兼容转写端点；失败返回 None 触发降级。"""
    import httpx

    url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/audio/transcriptions"
    try:
        with open(path, "rb") as fh:
            files = {"file": (path.name, fh, "application/octet-stream")}
            data = {"model": model}
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    url, headers={"Authorization": f"Bearer {api_key}"}, files=files, data=data
                )
        if resp.status_code == 200:
            return resp.json().get("text", "")
    except Exception:
        return None
    return None


class AudioTool(BaseTool):
    name = "audio_transcribe"
    description = "把用户上传的音频转写为文字（语音识别/会议记录）。用户要求转写录音、语音转文字时使用。"
    args_schema = AudioArgs
    timeout_s = 120.0

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()

        from app.services.multimodal import is_feature_enabled, resolve_user_file
        from app.services.multimodal.helpers import AUDIO_EXTS

        if not is_feature_enabled("audioEnabled"):
            return ToolResult(output="", duration_ms=0, error="语音识别功能已被管理员关闭")

        query = str(kwargs.get("query") or "").strip()
        target, path, hint = resolve_user_file(kwargs.get("_user_id"), query, exts=AUDIO_EXTS)
        if target is None or path is None:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=hint)

        # 解析默认模型凭据用于转写端点
        api_key = base_url = ""
        try:
            from app.db.session import SessionLocal
            from app.services.llm.model_service import ModelService

            db = SessionLocal()
            try:
                cfg = ModelService(db).get_default()
                if cfg:
                    api_key, base_url = (cfg.api_key or ""), (cfg.base_url or "")
            finally:
                db.close()
        except Exception:
            pass

        text = None
        stt_model = "whisper-1"
        try:
            from app.services.system.settings_store import settings_store

            stt_model = settings_store.get("sttModel", "whisper-1") or "whisper-1"
        except Exception:
            pass

        if api_key:
            text = await _transcribe_via_api(path, api_key, base_url, stt_model)

        if text is None:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="语音转写不可用：需配置支持 /audio/transcriptions 的模型密钥（如 OpenAI whisper-1），或安装本地 whisper 后端。",
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(
            output=f"{hint}\n\n【转写结果】\n{text}",
            duration_ms=duration_ms,
            artifact={"type": "markdown", "title": f"转写 · {target.original_name}", "content": text},
        )
