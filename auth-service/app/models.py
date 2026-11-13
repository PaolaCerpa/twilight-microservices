from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Conjunto(Base):
    __tablename__ = "conjuntos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    direccion: Mapped[str] = mapped_column(String(300), default="")
    ciudad: Mapped[str] = mapped_column(String(100), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Apartamento(Base):
    __tablename__ = "apartamentos"
    __table_args__ = (UniqueConstraint("conjunto_id", "bloque", "apto"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conjunto_id: Mapped[int] = mapped_column(ForeignKey("conjuntos.id"), index=True)
    bloque: Mapped[int] = mapped_column(Integer)
    apto: Mapped[str] = mapped_column(String(10))
    propietario: Mapped[str] = mapped_column(String(200), default="")
    telefono: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(254), default="")
    password: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)