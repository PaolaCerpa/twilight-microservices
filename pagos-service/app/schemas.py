from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

class PagoCrear(BaseModel):
    apartamento_id: int
    fecha: date
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    medio_pago: Literal["Efectivo", "Transferencia", "Cheque", "Otro"] = "Transferencia"
    referencia: str = Field(default="", max_length=100)
    observacion: str = Field(default="", max_length=200)


class PagoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conjunto_id: int
    apartamento_id: int
    fecha: date
    monto: Decimal
    medio_pago: str
    referencia: str
    observacion: str
    estado: str
    creado_en: datetime