from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)

PENDIENTE = "pendiente"
CONFIRMADO = "confirmado"
FALLIDO = "fallido"
ANULADO = "anulado"

MEDIOS_PAGO = ["Efectivo", "Transferencia", "Cheque", "Otro"]

class Pago(Base):
    __tablename__ = "Pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conjunto_id: Mapped[int] = mapped_column(Integer, index=True)
    apartamento_id: Mapped[int] = mapped_column(Integer, index=True)
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    medio_pago: Mapped[str] = mapped_column(String(20), default="Transferencia")
    referencia: Mapped[str] = mapped_column(String(100), default="")
    observacion: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[str] = mapped_column(String(20), default=PENDIENTE)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pago_id: Mapped[int] = mapped_column(Integer, index=True)
    tipo: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)
    procesado: Mapped[bool] = mapped_column(Boolean, default=False)
    intentos: Mapped[int] = mapped_column(Integer, default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)