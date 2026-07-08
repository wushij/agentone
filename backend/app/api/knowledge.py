"""backend/app/api/knowledge.py"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.common.pagination import clamp_page, page_result, slice_page
from app.common.response import success
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.file_service import FileService
from app.services.model_service import ModelService
from app.services.rag_service import RagService

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_KNOWLEDGE_JSON = _DATA_DIR / "knowledge.json"


def _load_kb() -> list[dict]:
    if not _KNOWLEDGE_JSON.exists():
        return []
    try:
        return json.loads(_KNOWLEDGE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_kb(kb_list: list[dict]):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _KNOWLEDGE_JSON.write_text(json.dumps(kb_list, ensure_ascii=False, indent=2), encoding="utf-8")


async def index_kb_files_task(
    kb_id: str,
    file_ids: list[str],
    chunk_size: int,
    chunk_overlap: int,
    user_id: int,
    db: Session,
    segment_delimiter: str = "paragraph",
):
    file_service = FileService(db)
    model_service = ModelService(db)
    default_model = model_service.get_default()
    
    api_key = default_model.api_key if default_model else None
    base_url = default_model.base_url if default_model else None
    model_name = default_model.model_name if default_model else "text-embedding-3-small"

    for fid in file_ids:
        f = file_service.get_file(user_id, fid)
        if f:
            await RagService.index_file_in_kb(
                kb_id=kb_id,
                file_id=fid,
                file_name=f.filename,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                segment_delimiter=segment_delimiter,
            )


@router.get("")
def list_knowledge(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    keyword: str = Query(default=""),
    user: User = Depends(get_current_user),
):
    all_kb = _load_kb()
    if keyword.strip():
        kw = keyword.strip().lower()
        all_kb = [
            kb
            for kb in all_kb
            if kw in str(kb.get("name", "")).lower() or kw in str(kb.get("description", "")).lower()
        ]
    page, size = clamp_page(page, size)
    records, total = slice_page(all_kb, page, size)
    return success(page_result(records, total))


@router.post("")
def create_knowledge(
    data: dict,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="知识库名称不能为空")

    kb_list = _load_kb()
    kb_id = f"kb_{uuid.uuid4().hex[:8]}"
    
    file_ids = data.get("fileIds", [])
    chunk_size = int(data.get("chunkSize", 500))
    chunk_overlap = int(data.get("chunkOverlap", 50))
    segment_delimiter = data.get("segmentDelimiter", "paragraph")
    
    new_kb = {
        "id": kb_id,
        "name": name,
        "description": data.get("description", "").strip(),
        "fileIds": file_ids,
        "chunkSize": chunk_size,
        "chunkOverlap": chunk_overlap,
        "segmentDelimiter": segment_delimiter,
        "embeddingModel": data.get("embeddingModel", "text-embedding-3-small"),
        "retrievalMode": data.get("retrievalMode", "hybrid"),
        "topK": int(data.get("topK", 3)),
        "scoreThreshold": float(data.get("scoreThreshold", 0.5)),
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    kb_list.append(new_kb)
    _save_kb(kb_list)

    if file_ids:
        background_tasks.add_task(
            index_kb_files_task,
            kb_id,
            file_ids,
            chunk_size,
            chunk_overlap,
            user.id,
            db,
            segment_delimiter,
        )

    return success(new_kb, message="创建成功，已提交后台进行智能文本分片与索引")


@router.put("/{kb_id}")
def update_knowledge(
    kb_id: str,
    data: dict,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    kb_list = _load_kb()
    target = None
    for kb in kb_list:
        if kb["id"] == kb_id:
            target = kb
            break

    if not target:
        raise HTTPException(status_code=404, detail="知识库不存在")

    old_file_ids = set(target.get("fileIds", []))
    
    name = data.get("name", "").strip()
    if name:
        target["name"] = name
    target["description"] = data.get("description", "").strip()
    
    file_ids = data.get("fileIds", [])
    target["fileIds"] = file_ids
    
    chunk_size = int(data.get("chunkSize", 500))
    chunk_overlap = int(data.get("chunkOverlap", 50))
    segment_delimiter = data.get("segmentDelimiter", target.get("segmentDelimiter", "paragraph"))
    target["chunkSize"] = chunk_size
    target["chunkOverlap"] = chunk_overlap
    target["segmentDelimiter"] = segment_delimiter
    
    target["embeddingModel"] = data.get("embeddingModel", "text-embedding-3-small")
    target["retrievalMode"] = data.get("retrievalMode", "hybrid")
    target["topK"] = int(data.get("topK", 3))
    target["scoreThreshold"] = float(data.get("scoreThreshold", 0.5))

    _save_kb(kb_list)

    # Find changes and reindex
    new_file_ids = set(file_ids)
    added_files = list(new_file_ids - old_file_ids)
    removed_files = list(old_file_ids - new_file_ids)

    # Clean removed files chunks
    for fid in removed_files:
        RagService.remove_file_chunks(kb_id, fid)

    # Index new files in background
    if added_files:
        background_tasks.add_task(
            index_kb_files_task,
            kb_id,
            added_files,
            chunk_size,
            chunk_overlap,
            user.id,
            db,
            segment_delimiter,
        )

    return success(target, message="更新成功，已提交新增文档的文本分片与索引")


def _build_preview_segments(
  data: dict,
  user_id: int,
  db: Session,
) -> tuple[list[dict], list[str], dict]:
    chunk_size = int(data.get("chunkSize", 500))
    chunk_overlap = int(data.get("chunkOverlap", 50))
    segment_delimiter = data.get("segmentDelimiter", "paragraph")
    file_ids = data.get("fileIds", [])

    file_service = FileService(db)
    segments: list[dict] = []
    file_errors: list[str] = []
    for fid in file_ids:
        f = file_service.get_file(user_id, fid)
        if not f:
            file_errors.append(f"文件 {fid} 不存在或无权访问")
            continue
        stored_path = file_service.resolve_path(f)
        if not stored_path.exists():
            file_errors.append(f"「{f.original_name}」在服务器上找不到物理文件，请重新上传")
            continue
        file_segments = RagService.build_file_preview_segments(
            fid,
            f.filename,
            display_name=f.original_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            segment_delimiter=segment_delimiter,
        )
        if not file_segments:
            file_errors.append(f"「{f.original_name}」解析后无有效文本，请检查文件内容或分段参数")
        segments.extend(file_segments)

    for i, seg in enumerate(segments, 1):
        seg["index"] = i

    delimiter_label = {
        "newline": "换行",
        "paragraph": "双换行（段落）",
        "none": "不分段（仅按长度切分）",
    }.get(segment_delimiter, segment_delimiter)

    meta = {
        "chunkSize": chunk_size,
        "chunkOverlap": chunk_overlap,
        "segmentDelimiter": segment_delimiter,
        "segmentDelimiterLabel": delimiter_label,
    }
    return segments, file_errors, meta


@router.get("/{kb_id}/preview")
def preview_knowledge(
    kb_id: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kb_list = _load_kb()
    kb = next((k for k in kb_list if k["id"] == kb_id), None)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    segments, file_errors, meta = _build_preview_segments(kb, user.id, db)
    page, size = clamp_page(page, size)
    paged, total = slice_page(segments, page, size)

    return success({
        "kbId": kb_id,
        "kbName": kb.get("name", ""),
        "total": total,
        **meta,
        "fileErrors": file_errors,
        "segments": paged,
    })


@router.post("/preview")
def preview_knowledge_draft(
    data: dict,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_ids = data.get("fileIds", [])
    if not file_ids:
        raise HTTPException(status_code=400, detail="请先选择关联文件")

    segments, file_errors, meta = _build_preview_segments(data, user.id, db)
    page, size = clamp_page(page, size)
    paged, total = slice_page(segments, page, size)

    return success({
        "kbId": data.get("id", ""),
        "kbName": data.get("name", "预览"),
        "total": total,
        **meta,
        "fileErrors": file_errors,
        "segments": paged,
    })


@router.delete("/{kb_id}")
def delete_knowledge(kb_id: str, user: User = Depends(get_current_user)):
    kb_list = _load_kb()
    kb_list = [kb for kb in kb_list if kb["id"] != kb_id]
    _save_kb(kb_list)
    
    # Remove all chunks associated with this knowledge base
    RagService.clear_kb_chunks(kb_id)
    return success(None, message="删除成功")
