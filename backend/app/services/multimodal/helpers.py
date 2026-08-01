"""app/services/multimodal/helpers.py — 多模态共享工具

- resolve_user_file：复用 FileService，按文件名关键词/扩展名类别定位用户上传文件；
- is_feature_enabled：按 settings_store 的功能开关做门控；
- image_to_data_url：图片转 base64 data URL（喂给多模态模型）。
"""

from __future__ import annotations

import base64
import mimetypes
from datetime import datetime
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".webm"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
DOC_EXTS = {".pdf", ".doc", ".docx", ".txt", ".md", ".markdown", ".xlsx", ".xls", ".csv"}

# 功能开关默认值（settings_store 未配置时的兜底）
_FEATURE_DEFAULTS = {
    "imageEnabled": True,
    "ocrEnabled": True,
    "documentEnabled": True,
    "audioEnabled": True,
    "videoEnabled": True,
}


def is_feature_enabled(key: str) -> bool:
    """多模态功能开关门控：settings_store.<key> 优先，回退默认（多为 True）。"""
    try:
        from app.services.system.settings_store import settings_store

        return bool(settings_store.get(key, _FEATURE_DEFAULTS.get(key, True)))
    except Exception:
        return _FEATURE_DEFAULTS.get(key, True)


def _score_filename(query: str, f_id: str, filename: str) -> int:
    q = (query or "").lower().strip()
    f = filename.lower()
    fid = (f_id or "").lower()
    if not q:
        return 0
    # 优先匹配文件 ID (如 file_86611543d3cb458d99f29584abb1e9c6)
    import re
    fid_match = re.search(r"file_[a-zA-Z0-9_\-]+", q)
    if fid_match and fid_match.group(0).lower() == fid:
        return 500
    alt_match = re.search(r"!\[(.*?)\]", q)
    if alt_match:
        alt = alt_match.group(1).lower().strip()
        if alt and (alt == f or alt in f):
            return 300
    if q == f:
        return 200
    if f.endswith(q) or f.startswith(q):
        return 150
    if q in f:
        return 120 + len(q)
    tokens = [t for t in q.replace(".", " ").split() if len(t) >= 2]
    return sum(30 for t in tokens if t in f)


def resolve_user_file(user_id: int | str | None, query: str, *, exts: set[str] | None = None):
    """定位用户上传文件，返回 (FileAsset|None, Path|None, hint)。

    query 可包含完整 prompt / markdown；支持提取 file_id 与文件名精准匹配；
    留空或无法精准匹配时自动取该类别下最近上传的一个。
    """
    if not user_id:
        return None, None, "无法识别用户上下文"
    from app.db.session import SessionLocal
    from app.services.file.file_service import FileService

    db = SessionLocal()
    try:
        svc = FileService(db)
        files, _ = svc.list_files(int(user_id), page=1, size=500)
        if exts:
            files = [f for f in files if Path(f.original_name).suffix.lower() in exts]
        if not files:
            cat = "该类型" if exts else ""
            return None, None, f"当前用户暂无已上传的{cat}文件，请先在对话或文件中心上传。"

        if not query:
            target = files[0]  # list_files 已按创建时间倒序
            hint = f"已自动选择最近上传的「{target.original_name}」"
        else:
            scored = sorted(
                ((f, _score_filename(query, f.id, f.original_name)) for f in files),
                key=lambda it: (it[1], it[0].created_at or datetime.min),
                reverse=True,
            )
            target, best = scored[0]
            if best <= 0:
                target = files[0]
                hint = f"已自动选择最近上传的「{target.original_name}」"
            else:
                hint = f"已匹配文件「{target.original_name}」"
        return target, svc.resolve_path(target), hint
    finally:
        db.close()


def image_to_data_url(path: Path) -> str:
    data = Path(path).read_bytes()
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"
