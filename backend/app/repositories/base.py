"""app/repositories/base.py — 通用 BaseRepository 数据仓储基类"""

from typing import Any, Generic, Sequence, TypeVar
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):

    def __init__(self, model: type[ModelType], db: Session | None = None):
        self.model = model
        self.db = db

    def get(self, db_or_id: Any, id: Any = None) -> ModelType | None:
        if isinstance(db_or_id, Session):
            return db_or_id.get(self.model, id)
        elif self.db is not None:
            return self.db.get(self.model, db_or_id)
        raise ValueError("Session is required")

    def get_by_id(self, db_or_id: Any, id: Any = None) -> ModelType | None:
        return self.get(db_or_id, id)

    def get_multi(
        self, db: Session | None = None, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        session = db or self.db
        if not session:
            raise ValueError("Session is required")
        stmt = select(self.model).offset(skip).limit(limit)
        return session.scalars(stmt).all()

    def create(self, db_or_obj: Any = None, *, obj_in: dict[str, Any] | None = None) -> ModelType:
        if isinstance(db_or_obj, Session):
            session = db_or_obj
            data = obj_in or {}
        else:
            session = self.db
            data = db_or_obj or obj_in or {}
        if not session:
            raise ValueError("Session is required")
        db_obj = self.model(**data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(
        self, db_or_obj: Any, db_obj: ModelType | None = None, obj_in: dict[str, Any] | None = None
    ) -> ModelType:
        if isinstance(db_or_obj, Session):
            session = db_or_obj
            target_obj = db_obj
            data = obj_in or {}
        else:
            session = self.db
            target_obj = db_or_obj
            data = db_obj or obj_in or {}
        if not session or not target_obj:
            raise ValueError("Session and target object are required")
        for field, value in data.items():
            if hasattr(target_obj, field):
                setattr(target_obj, field, value)
        session.add(target_obj)
        session.commit()
        session.refresh(target_obj)
        return target_obj

    def remove(self, db_or_id: Any, id: Any = None) -> ModelType | None:
        if isinstance(db_or_id, Session):
            session = db_or_id
            target_id = id
        else:
            session = self.db
            target_id = db_or_id
        if not session:
            raise ValueError("Session is required")
        obj = session.get(self.model, target_id)
        if obj:
            session.delete(obj)
            session.commit()
        return obj
