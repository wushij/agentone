"""backend/app/services/model_service.py"""

from __future__ import annotations

import time
from decimal import Decimal

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.model_config import ModelConfig


class ModelService:
    def __init__(self, db: Session):
        self.db = db

    def list_models(self, *, page: int = 1, size: int = 10) -> tuple[list[ModelConfig], int]:
        count_stmt = select(func.count()).select_from(ModelConfig)
        total = int(self.db.scalar(count_stmt) or 0)
        rows = list(
            self.db.scalars(
                select(ModelConfig)
                .order_by(ModelConfig.id)
                .offset((page - 1) * size)
                .limit(size)
            ).all()
        )
        return rows, total

    def get_by_name(self, name: str) -> ModelConfig | None:
        return self.db.scalar(select(ModelConfig).where(ModelConfig.name == name))

    def get_default(self) -> ModelConfig | None:
        row = self.db.scalar(select(ModelConfig).where(ModelConfig.is_default == 1, ModelConfig.status == 1))
        if row:
            return row
        return self.db.scalar(select(ModelConfig).where(ModelConfig.status == 1).limit(1))

    def resolve_model(self, model_id: str | None) -> ModelConfig | None:
        if model_id:
            row = self.get_by_name(model_id)
            if row and row.status == 1:
                return row
        return self.get_default()

    def create(self, data: dict) -> ModelConfig:
        if data.get("isDefault"):
            self._clear_default()
        row = ModelConfig(
            name=data["name"],
            provider=data["provider"],
            api_key=data.get("apiKey"),
            base_url=data.get("baseUrl"),
            model_name=data.get("modelName") or data["name"],
            temperature=Decimal(str(data.get("temperature", 0.7))),
            is_default=1 if data.get("isDefault") else 0,
            status=1 if data.get("status", "enabled") != "disabled" else 0,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, name: str, data: dict) -> ModelConfig | None:
        row = self.get_by_name(name)
        if row is None:
            return None
        if data.get("isDefault"):
            self._clear_default()
            row.is_default = 1
        if "name" in data and data["name"] is not None:
            row.name = data["name"]
        if "provider" in data and data["provider"] is not None:
            row.provider = data["provider"]
        if "apiKey" in data and data["apiKey"]:
            row.api_key = data["apiKey"]
        if "baseUrl" in data and data["baseUrl"] is not None:
            row.base_url = data["baseUrl"]
        if "modelName" in data and data["modelName"] is not None:
            row.model_name = data["modelName"]
        if "temperature" in data and data["temperature"] is not None:
            row.temperature = Decimal(str(data["temperature"]))
        if "status" in data and data["status"] is not None:
            row.status = 0 if data["status"] == "disabled" else 1
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, name: str) -> bool:
        row = self.get_by_name(name)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def set_default(self, name: str) -> ModelConfig | None:
        row = self.get_by_name(name)
        if row is None:
            return None
        self._clear_default()
        row.is_default = 1
        row.status = 1
        self.db.commit()
        self.db.refresh(row)
        return row

    def _clear_default(self) -> None:
        rows, _ = self.list_models(page=1, size=500)
        for row in rows:
            if row.is_default:
                row.is_default = 0
        self.db.flush()

    def _resolve_api_credentials(self, row: ModelConfig) -> tuple[str, str]:
        api_key = row.api_key or ""
        base_url = row.base_url or ""
        if row.provider == "deepseek":
            settings = get_settings()
            api_key = api_key or settings.DEEPSEEK_API_KEY
            base_url = base_url or settings.DEEPSEEK_BASE_URL
        if not api_key:
            raise ValueError("API Key 未配置")
        return api_key, base_url

    @staticmethod
    def _openai_compatible_base_url(base_url: str) -> str:
        root = base_url.rstrip("/")
        return root if root.endswith("/v1") else f"{root}/v1"

    async def test_connection(self, name: str) -> dict:
        row = self.get_by_name(name)
        if row is None:
            raise ValueError("模型不存在")
        if row.provider == "mock":
            return {"ok": True, "model": name, "latencyMs": 12}

        api_key, base_url = self._resolve_api_credentials(row)
        endpoint = f"{self._openai_compatible_base_url(base_url)}/chat/completions"
        timeout = httpx.Timeout(15.0, connect=5.0)
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": row.model_name,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                        "stream": False,
                    },
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ValueError("连接超时（15s），请检查网络或 Base URL") from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:200] if exc.response is not None else str(exc)
            raise ValueError(f"连接失败: HTTP {exc.response.status_code} {detail}") from exc
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"连接失败: {exc}") from exc

        latency = int((time.perf_counter() - start) * 1000)
        return {"ok": True, "model": name, "latencyMs": latency}

    def to_dict(self, row: ModelConfig, *, mask_key: bool = True) -> dict:
        api_key = row.api_key or ""
        masked = f"{api_key[:4]}***{api_key[-4:]}" if mask_key and len(api_key) > 8 else ("***" if api_key else "")
        return {
            "name": row.name,
            "provider": row.provider,
            "modelName": row.model_name,
            "baseUrl": row.base_url or "",
            "apiKey": masked,
            "hasApiKey": bool(row.api_key),
            "temperature": float(row.temperature),
            "status": "enabled" if row.status == 1 else "disabled",
            "isDefault": row.is_default == 1,
        }

    def seed_defaults(self) -> None:
        _, total = self.list_models(page=1, size=1)
        if total:
            return
        settings = get_settings()
        self.create(
            {
                "name": "mock-chat",
                "provider": "mock",
                "modelName": "mock-chat",
                "temperature": 0.7,
                "isDefault": settings.LLM_PROVIDER == "mock",
                "status": "enabled",
            }
        )
        if settings.DEEPSEEK_API_KEY or settings.LLM_PROVIDER == "deepseek":
            self.create(
                {
                    "name": settings.DEEPSEEK_MODEL,
                    "provider": "deepseek",
                    "modelName": settings.DEEPSEEK_MODEL,
                    "baseUrl": settings.DEEPSEEK_BASE_URL,
                    "apiKey": settings.DEEPSEEK_API_KEY,
                    "temperature": 0.7,
                    "isDefault": settings.LLM_PROVIDER == "deepseek",
                    "status": "enabled" if settings.DEEPSEEK_API_KEY else "disabled",
                }
            )
