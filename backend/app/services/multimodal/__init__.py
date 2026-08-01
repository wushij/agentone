"""app/services/multimodal — 多模态处理服务集（图像/OCR/文档/音频/视频）

设计原则（与项目一致）：
- API 优先：图像理解/OCR 默认走多模态大模型（Qwen-VL/GPT-4o/Gemini），零重依赖；
- 优雅降级：本地重库（PaddleOCR/whisper/ffmpeg）为可选，未安装则清晰提示而非崩溃；
- 复用现有设施：文件定位复用 FileService，文档解析复用 rag.parser，产物登记复用 Artifact。
"""

from app.services.multimodal.helpers import (
    IMAGE_EXTS,
    is_feature_enabled,
    resolve_user_file,
)
from app.services.multimodal.vision import vision_chat

__all__ = [
    "IMAGE_EXTS",
    "is_feature_enabled",
    "resolve_user_file",
    "vision_chat",
]
