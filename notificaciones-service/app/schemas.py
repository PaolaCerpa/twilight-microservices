from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NotificacionCrear(BaseModel):
    conjunto_id: int | None = None
    apartamento_id: int | None = None
    tipo: str = Field(default="general", max_length=30)
    mensaje: str = Field(min_length=1)

    @model_validator(mode="after")
    def validar_destino(self) -> Self:
        if self.conjunto_id is None and self.apartamento_id is None:
            raise ValueError(
                "Debe proporcionar al menos un conjunto_id o un apartamento_id para crear una notificación."
            )
        return self


class NotificacionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conjunto_id: int
    apartamento_id: int | None
    tipo: str
    mensaje: str
    leida: bool
    creado_en: datetime