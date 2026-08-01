"""app/services/multimodal/vision.py — 视觉模型调用（图像理解 / OCR）

核心思路：聊天模型（如 DeepSeek）不支持视觉时，多模态工具自动切换到系统里已配置的
「视觉模型」（qwen-vl / gpt-4o / gemini / claude-3 / glm-4v 等）来看图，聊天本身不受影响。

视觉模型选取优先级：
  1) 显式传入 model_id；
  2) settings_store.visionModel 指定的模型名（且该模型存在且启用）；
  3) 扫描已配置模型，按 model_name 自动识别出一个视觉模型；
  4) 都没有 → 抛出可执行的指引（提示去管理后台加一个视觉模型）。
"""

from __future__ import annotations

from pathlib import Path

from app.utils.logger import logger

# 视觉模型识别特征（对 model_name 做小写子串匹配）
_VISION_HINTS = (
    "vl", "vision", "gpt-4o", "4o", "gemini", "claude-3", "claude-sonnet",
    "claude-opus", "claude-haiku", "glm-4v", "glm-4.1v", "step-1v", "step-1o",
    "llava", "pixtral", "internvl", "minicpm-v", "yi-vision", "doubao-vision",
    "grok-vision", "grok-2-vision", "qvq",
)

_NO_VISION_MODEL_MSG = (
    "系统尚未配置支持视觉的模型，无法看图。"
    "请在【管理后台 → 模型管理】新增一个视觉模型（如 qwen-vl-plus / qwen-vl-max / gpt-4o / gemini-1.5-pro / glm-4v），"
    "填好对应的 API Key 即可；无需改动聊天所用的 DeepSeek 模型。"
    "（也可在系统设置里用 visionModel 指定要用的视觉模型名。）"
)


def _looks_like_vision(model_name: str) -> bool:
    name = (model_name or "").lower()
    return any(h in name for h in _VISION_HINTS)


def _resolve_vision_model_name(explicit: str | None = None) -> str | None:
    """解析出用于视觉/图片分析的模型名称。若无专属视觉模型，回退系统默认模型（纯文本模型将走多模态工具降级抽取）。"""
    if explicit:
        return explicit
    try:
        from app.db.session import SessionLocal
        from app.services.llm.model_service import ModelService
        from app.services.system.settings_store import settings_store

        configured = (settings_store.get("visionModel", "") or "").strip()
        db = SessionLocal()
        try:
            svc = ModelService(db)
            # 1) 显式配置的 visionModel（存在且启用）
            if configured:
                row = svc.get_by_name(configured)
                if row and row.status == 1:
                    return row.name
            # 2) 自动识别：扫描启用的模型，命中视觉特征者优先
            rows, _ = svc.list_models(page=1, size=500)
            active_rows = [r for r in rows if r.status == 1]
            for row in active_rows:
                if _looks_like_vision(row.model_name) or _looks_like_vision(row.name):
                    return row.name
            # 3) 若无专属视觉模型，取当前默认激活的模型 (如 DeepSeek)，交由多模态降级适配器处理
            default_model = settings_store.get("defaultModel", "")
            if default_model:
                row = svc.get_by_name(default_model)
                if row and row.status == 1:
                    return row.name
            if active_rows:
                return active_rows[0].name
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"[Vision] 解析视觉模型失败: {exc}")
    return None


async def vision_chat(image_path: str | Path, prompt: str, *, model_id: str | None = None) -> str:
    """对单张图片提问/描述。

    若模型支持 Vision 原生协议，直接进行视觉识别；
    若目标模型为纯文本大模型（如 DeepSeek，抛出 unknown variant `image_url` 400 错误），
    则通过多模态工具提取图像文本与元数据，无缝转译为纯文本格式喂给大模型，使其获得看图能力！
    """
    from langchain_core.messages import HumanMessage

    from app.llm.factory import create_chat_model
    from app.services.multimodal.helpers import image_to_data_url

    vision_model = _resolve_vision_model_name(model_id)
    if not vision_model:
        raise RuntimeError(_NO_VISION_MODEL_MSG)

    path_obj = Path(image_path)
    data_url = image_to_data_url(path_obj)
    llm = create_chat_model(model=vision_model)
    message = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": data_url}},
    ])
    try:
        resp = await llm.ainvoke([message])
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as exc:
        err_msg = str(exc)
        # 判断是否为纯文本大模型（如 DeepSeek）拒绝 image_url 格式的 400 错误
        if any(k in err_msg for k in ("unknown variant `image_url`", "image_url", "expected `text`", "400")):
            logger.info(f"[Vision] 模型「{vision_model}」不支持原生 image_url，触发多模态工具纯文本降级转译")
            ocr_text = ""
            try:
                from app.knowledge.loader import load_document
                res = load_document(path_obj)
                ocr_text = res.get("content", "").strip()
            except Exception as ocr_exc:
                logger.debug(f"[Vision] OCR 提取跳过: {ocr_exc}")

            img_name = path_obj.name
            if ocr_text:
                context_str = f"【多模态工具已解析图片「{img_name}」的内容】：\n{ocr_text}"
            else:
                context_str = f"【多模态工具已接收图片「{img_name}」】"

            text_msg = HumanMessage(content=f"{context_str}\n\n用户问题：{prompt}")
            try:
                resp = await llm.ainvoke([text_msg])
                return resp.content if isinstance(resp.content, str) else str(resp.content)
            except Exception as inner_exc:
                logger.warning(f"[Vision] 纯文本降级处理失败: {inner_exc}")
                raise RuntimeError(f"多模态处理失败：{inner_exc}") from inner_exc

        logger.warning(f"[Vision] 视觉模型 {vision_model} 调用失败: {exc}")
        raise RuntimeError(f"视觉模型调用失败：{exc}") from exc
