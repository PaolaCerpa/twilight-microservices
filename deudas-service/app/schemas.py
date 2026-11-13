from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CargoCrear(BaseModel):
    apartamento_id: int
    periodo: date
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    concepto: str = Field(default="Cuota administración", max_length=200)


class CargoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conjunto_id: int
    apartamento_id: int
    periodo: date
    concepto: str
    monto: Decimal


class MovimientoPago(BaseModel):
    pago_id: int
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class EstadoRespuesta(BaseModel):
    conjunto_id: int
    apartamento_id: int
    estado_gestion: str
    total_pagado: Decimal
    saldo: Decimal
    notas: str | None
    actualizado_en: datetime