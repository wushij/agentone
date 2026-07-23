"""backend/app/api/models.py"""



from __future__ import annotations



from fastapi import APIRouter, Depends, Query

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session



from app.utils.pagination import clamp_page, page_result
from app.utils.response import success

from app.api.deps import require_permission

from app.db.session import get_db

from app.models.user import User

from app.services.llm.model_service import ModelService



router = APIRouter(prefix="/api/models", tags=["模型"])





class ModelCreateRequest(BaseModel):

    name: str

    provider: str

    model_name: str = Field(alias="modelName")

    base_url: str | None = Field(default=None, alias="baseUrl")

    api_key: str | None = Field(default=None, alias="apiKey")

    temperature: float = 0.7

    is_default: bool = Field(default=False, alias="isDefault")

    status: str = "enabled"



    model_config = {"populate_by_name": True}





class ModelUpdateRequest(BaseModel):

    name: str | None = None

    provider: str | None = None

    model_name: str | None = Field(default=None, alias="modelName")

    base_url: str | None = Field(default=None, alias="baseUrl")

    api_key: str | None = Field(default=None, alias="apiKey")

    temperature: float | None = None

    is_default: bool | None = Field(default=None, alias="isDefault")

    status: str | None = None



    model_config = {"populate_by_name": True}





@router.get("/available")
def list_available_models(
    user: User = Depends(require_permission("chat:read")),
    db: Session = Depends(get_db),
):
    svc = ModelService(db)
    rows, _ = svc.list_models(page=1, size=500)
    items = [
        {
            "name": m.name,
            "modelName": m.model_name,
            "provider": m.provider,
            "isDefault": m.is_default == 1,
        }
        for m in rows
        if m.status == 1
    ]
    return success(items)


@router.get("")

def list_models(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user: User = Depends(require_permission("model:manage")),
    db: Session = Depends(get_db),
):

    svc = ModelService(db)
    page, size = clamp_page(page, size)
    rows, total = svc.list_models(page=page, size=size)
    records = [svc.to_dict(m) for m in rows]
    return success(page_result(records, total))





@router.post("")

def create_model(

    body: ModelCreateRequest,

    user: User = Depends(require_permission("model:manage")),

    db: Session = Depends(get_db),

):

    svc = ModelService(db)

    row = svc.create(body.model_dump(by_alias=True))

    return success(svc.to_dict(row), message="创建成功")





@router.put("/{name}")

def update_model(

    name: str,

    body: ModelUpdateRequest,

    user: User = Depends(require_permission("model:manage")),

    db: Session = Depends(get_db),

):

    svc = ModelService(db)

    row = svc.update(name, body.model_dump(by_alias=True, exclude_none=True))

    if row is None:

        raise ValueError("模型不存在")

    return success(svc.to_dict(row), message="更新成功")





@router.delete("/{name}")

def delete_model(

    name: str,

    user: User = Depends(require_permission("model:manage")),

    db: Session = Depends(get_db),

):

    if not ModelService(db).delete(name):

        raise ValueError("模型不存在")

    return success(None, message="已删除")





@router.post("/{name}/default")

def set_default_model(

    name: str,

    user: User = Depends(require_permission("model:manage")),

    db: Session = Depends(get_db),

):

    svc = ModelService(db)

    row = svc.set_default(name)

    if row is None:

        raise ValueError("模型不存在")

    return success(svc.to_dict(row), message="已设为默认")





@router.post("/{name}/test")

async def test_model(

    name: str,

    user: User = Depends(require_permission("model:manage")),

    db: Session = Depends(get_db),

):

    result = await ModelService(db).test_connection(name)

    return success(result, message="连接成功")