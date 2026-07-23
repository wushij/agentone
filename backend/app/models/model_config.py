"""backend/app/models/model_config.py"""

from decimal import Decimal

from sqlalchemy import BigInteger, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    provider: Mapped[str] = mapped_column(String(64))
    api_key: Mapped[str | None] = mapped_column(String(512))
    base_url: Mapped[str | None] = mapped_column(String(512))
    model_name: Mapped[str] = mapped_column(String(128))
    temperature: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.70"))
    is_default: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)