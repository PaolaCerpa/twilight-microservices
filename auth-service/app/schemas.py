from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class LoginCrear(BaseModel):
    conjunto: int
    bloque: int
    apto: str = Field(min_length=1, max_length=10)
    password: str = Field(min_length=1)


class ConjuntoCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    direccion: str = Field(default="", max_length=300)
    ciudad: str = Field(default="", max_length=100)


class ConjuntoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    direccion: str
    ciudad: str
    activo: bool


class ApartamentoCrear(BaseModel):
    conjunto: int
    bloque: int
    apto: str = Field(min_length=1, max_length=10)
    propietario: str = Field(default="", max_length=200)
    telefono: str = Field(default="", max_length=20)
    email: str = Field(default="", max_length=254)
    password: str = Field(min_length=8)


class ApartamentoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conjunto: int = Field(validation_alias=AliasChoices("conjunto_id", "conjunto"))
    bloque: int
    apto: str
    propietario: str
    telefono: str
    email: str
    activo: bool


class LoginRespuesta(BaseModel):
    token: str
    apartamento: ApartamentoRespuesta