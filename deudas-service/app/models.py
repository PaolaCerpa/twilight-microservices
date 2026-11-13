from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

NORMAL = "Normal"
PRE_JURIDICO = "Pre-Juridico"
JURIDICO = "Juridico"
ACUERDO = "Acuerdo"
ESTADOS = [NORMAL, PRE_JURIDICO, JURIDICO, ACUERDO]


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Cargo(Base):
    __tablename__ = "cargos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conjunto_id: Mapped[int] = mapped_column(Integer, index=True)
    apartamento_id: Mapped[int] = mapped_column(Integer, index=True)
    periodo: Mapped[date] = mapped_column(Date)
    concepto: Mapped[str] = mapped_column(String(200), default="Cuota administración")
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class EstadoApartamento(Base):
    __tablename__ = "estados_apartamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conjunto_id: Mapped[int] = mapped_column(Integer, index=True)
    apartamento_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    estado_gestion: Mapped[str] = mapped_column(String(20), default=NORMAL)
    total_pagado: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=ahora_utc, onupdate=ahora_utc
    )


class PagoAplicado(Base):
    __tablename__ = "pagos_aplicados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pago_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    apartamento_id: Mapped[int] = mapped_column(Integer, index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    revertido: Mapped[bool] = mapped_column(Boolean, default=False)
    aplicado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)