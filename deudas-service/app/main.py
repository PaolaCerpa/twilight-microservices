from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .clients import ServicioNoDisponible, obtener_apartamento
from .database import Base, engine, get_db
from .models import Cargo, EstadoApartamento, PagoAplicado
from .reglas import actualizar_estado, saldo
from .schemas import CargoCrear, CargoRespuesta, EstadoRespuesta, MovimientoPago


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="deudas-service", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def errores_de_validacion(request: Request, exc: RequestValidationError):
    errores = {}
    for e in exc.errors():
        campo = str(e["loc"][-1]) if e["loc"] else "body"
        mensaje = "Este campo es requerido." if e["type"] == "missing" else e["msg"]
        errores.setdefault(campo, []).append(mensaje)
    return JSONResponse(status_code=400, content=errores)


def buscar_estado(db: Session, apartamento_id: int) -> EstadoApartamento | None:
    return (
        db.query(EstadoApartamento)
        .filter(EstadoApartamento.apartamento_id == apartamento_id)
        .first()
    )


def respuesta_estado(db: Session, estado: EstadoApartamento) -> EstadoRespuesta:
    return EstadoRespuesta(
        conjunto_id=estado.conjunto_id,
        apartamento_id=estado.apartamento_id,
        estado_gestion=estado.estado_gestion,
        total_pagado=estado.total_pagado,
        saldo=saldo(db, estado),
        notas=estado.notas,
        actualizado_en=estado.actualizado_en,
    )


@app.post("/deudas/cargos/", response_model=CargoRespuesta, status_code=201)
def crear_cargo(datos: CargoCrear, db: Session = Depends(get_db)):
    try:
        apartamento = obtener_apartamento(datos.apartamento_id)
    except ServicioNoDisponible:
        return JSONResponse(status_code=503, content={"error": "auth-service no está disponible."})
    if apartamento is None:
        return JSONResponse(status_code=404, content={"error": "El apartamento no existe."})

    conjunto_id = apartamento["conjunto"]
    cargo = Cargo(conjunto_id=conjunto_id, **datos.model_dump())
    db.add(cargo)

    estado = buscar_estado(db, datos.apartamento_id)
    if estado is None:
        estado = EstadoApartamento(conjunto_id=conjunto_id, apartamento_id=datos.apartamento_id)
        db.add(estado)

    db.flush()  
    actualizar_estado(db, estado)
    db.commit()
    db.refresh(cargo)
    return cargo


@app.get("/deudas/{apartamento_id}/", response_model=EstadoRespuesta)
def deuda_actual(apartamento_id: int, db: Session = Depends(get_db)):
    estado = buscar_estado(db, apartamento_id)
    if estado is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Este apartamento no tiene registro de deudas aún."},
        )
    return respuesta_estado(db, estado)


@app.get("/deudas/{apartamento_id}/historial/", response_model=list[CargoRespuesta])
def historial_deuda(apartamento_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Cargo)
        .filter(Cargo.apartamento_id == apartamento_id)
        .order_by(Cargo.periodo.desc())
        .all()
    )


@app.post("/deudas/{apartamento_id}/actualizar/", response_model=EstadoRespuesta)
def actualizar_deuda(apartamento_id: int, datos: MovimientoPago, db: Session = Depends(get_db)):
    estado = buscar_estado(db, apartamento_id)
    if estado is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Este apartamento no tiene registros de deudas"},
        )

    ya_aplicado = (
        db.query(PagoAplicado).filter(PagoAplicado.pago_id == datos.pago_id).first()
    )
    if ya_aplicado is None:  
        db.add(
            PagoAplicado(
                pago_id=datos.pago_id, apartamento_id=apartamento_id, monto=datos.monto
            )
        )
        try:
            db.flush()  
        except IntegrityError:
            db.rollback()
        else:
            estado.total_pagado = EstadoApartamento.total_pagado + datos.monto
            db.flush()
            db.refresh(estado)
            actualizar_estado(db, estado)
            db.commit()
        estado = buscar_estado(db, apartamento_id)

    return respuesta_estado(db, estado)


@app.post("/deudas/{apartamento_id}/revertir/", response_model=EstadoRespuesta)
def revertir_deuda(apartamento_id: int, datos: MovimientoPago, db: Session = Depends(get_db)):
    estado = buscar_estado(db, apartamento_id)
    aplicado = (
        db.query(PagoAplicado)
        .filter(
            PagoAplicado.pago_id == datos.pago_id,
            PagoAplicado.apartamento_id == apartamento_id,
        )
        .first()
    )
    if estado is None or aplicado is None:
        return JSONResponse(
            status_code=404,
            content={"error": "No existe un pago aplicado con ese pago_id para este apartamento."},
        )

    if not aplicado.revertido:
        cambiados = (
            db.query(PagoAplicado)
            .filter(PagoAplicado.id == aplicado.id, PagoAplicado.revertido.is_(False))
            .update({"revertido": True}, synchronize_session=False)
        )
        if cambiados == 1:
            estado.total_pagado = EstadoApartamento.total_pagado - aplicado.monto
            db.flush()
            db.refresh(estado)
            actualizar_estado(db, estado)
        db.commit()
        estado = buscar_estado(db, apartamento_id)

    return respuesta_estado(db, estado)