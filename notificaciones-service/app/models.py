from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conjunto_id: Mapped[int] = mapped_column(Integer, index=True)
    apartamento_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), default="general")
    mensaje: Mapped[str] = mapped_column(Text)
    leida: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)