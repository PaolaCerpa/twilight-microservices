from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .clients import ServicioNoDisponible, listar_apartamentos, obtener_apartamento
from .database import Base, engine, get_db
from .models import ACUERDO, JURIDICO, NORMAL, PRE_JURIDICO, Cargo, EstadoApartamento, PagoAplicado 
from .reglas import CENTAVOS, actualizar_estado, saldo
from .schemas import (
    CargoCrear,
    CargoMasivo,
    CargoRespuesta,
    EstadoRespuesta,
    FilaDeuda,
    GestionActualizar,
    MovimientoPago,
    ResultadoMasivo,
    ResumenConjunto,
)

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


def _crear_cargo(datos: CargoCrear, db: Session, *, conjunto_esperado: int | None):
    try:
        apartamento = obtener_apartamento(datos.apartamento_id)
    except ServicioNoDisponible:
        return JSONResponse(status_code=503, content={"error": "auth-service no está disponible."})
    if apartamento is None:
        return JSONResponse(status_code=404, content={"error": "El apartamento no existe."})
    if conjunto_esperado is not None and apartamento["conjunto"] != conjunto_esperado:
        return JSONResponse(
            status_code=404,
            content={"error": "El apartamento no existe en este conjunto."},
        )

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


@app.post("/deudas/cargos/", response_model=CargoRespuesta, status_code=201)
def crear_cargo(datos: CargoCrear, db: Session = Depends(get_db)):
    return _crear_cargo(datos, db, conjunto_esperado=None)


@app.post(
    "/deudas/conjunto/{conjunto_id}/cargos/",
    response_model=CargoRespuesta,
    status_code=201,
)
def crear_cargo_del_conjunto(
    conjunto_id: int, datos: CargoCrear, db: Session = Depends(get_db)
):
    return _crear_cargo(datos, db, conjunto_esperado=conjunto_id)


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


def filas_del_conjunto(db: Session, conjunto_id: int) -> list[FilaDeuda]:
    cargos = dict(
        db.query(Cargo.apartamento_id, func.sum(Cargo.monto))
        .filter(Cargo.conjunto_id == conjunto_id)
        .group_by(Cargo.apartamento_id)
        .all()
    )
    estados = (
        db.query(EstadoApartamento)
        .filter(EstadoApartamento.conjunto_id == conjunto_id)
        .order_by(EstadoApartamento.apartamento_id)
        .all()
    )
    filas = []
    for e in estados:
        total_cargos = Decimal(str(cargos.get(e.apartamento_id, 0))).quantize(CENTAVOS)
        total_pagado = Decimal(str(e.total_pagado)).quantize(CENTAVOS)
        filas.append(
            FilaDeuda(
                apartamento_id=e.apartamento_id,
                estado_gestion=e.estado_gestion,
                total_cargos=total_cargos,
                total_pagado=total_pagado,
                saldo=total_cargos - total_pagado,
                notas=e.notas,
            )
        )
    return filas


@app.get("/deudas/conjunto/{conjunto_id}/", response_model=list[FilaDeuda])
def deudas_del_conjunto(conjunto_id: int, db: Session = Depends(get_db)):
    return filas_del_conjunto(db, conjunto_id)


@app.get("/deudas/conjunto/{conjunto_id}/resumen/", response_model=ResumenConjunto)
def resumen_del_conjunto(conjunto_id: int, db: Session = Depends(get_db)):
    filas = filas_del_conjunto(db, conjunto_id)
    return ResumenConjunto(
        total_deuda=sum((f.saldo for f in filas if f.saldo > 0), Decimal("0")),
        total_recaudado=sum((f.total_pagado for f in filas), Decimal("0")),
        deudores=sum(1 for f in filas if f.saldo > 0),
        pre_juridicos=sum(1 for f in filas if f.estado_gestion == PRE_JURIDICO),
        juridicos=sum(1 for f in filas if f.estado_gestion == JURIDICO),
        acuerdos=sum(1 for f in filas if f.estado_gestion == ACUERDO),
    )


@app.get("/deudas/conjunto/{conjunto_id}/cargos/", response_model=list[CargoRespuesta])
def cargos_del_conjunto(conjunto_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Cargo)
        .filter(Cargo.conjunto_id == conjunto_id)
        .order_by(Cargo.periodo.desc(), Cargo.id.desc())
        .all()
    )


@app.delete("/deudas/conjunto/{conjunto_id}/cargos/{cargo_id}/")
def eliminar_cargo(conjunto_id: int, cargo_id: int, db: Session = Depends(get_db)):
    cargo = (
        db.query(Cargo)
        .filter(Cargo.id == cargo_id, Cargo.conjunto_id == conjunto_id)
        .first()
    )
    if cargo is None:
        return JSONResponse(status_code=404, content={"error": "Cuota no encontrada."})

    apartamento_id = cargo.apartamento_id
    db.delete(cargo)
    db.flush()
    estado = buscar_estado(db, apartamento_id)
    if estado is not None:
        actualizar_estado(db, estado)
    db.commit()
    return {"eliminado": True}


@app.post("/deudas/conjunto/{conjunto_id}/cargos/masivo/", response_model=ResultadoMasivo)
def generar_cargos_masivos(
    conjunto_id: int, datos: CargoMasivo, db: Session = Depends(get_db)
):
    try:
        apartamentos = listar_apartamentos(conjunto_id)
    except ServicioNoDisponible:
        return JSONResponse(status_code=503, content={"error": "auth-service no está disponible."})

    activos = [a["id"] for a in apartamentos if a["activo"]]
    ya_tienen = {
        fila[0]
        for fila in db.query(Cargo.apartamento_id).filter(
            Cargo.conjunto_id == conjunto_id,
            Cargo.periodo == datos.periodo,
            Cargo.concepto == datos.concepto,
        )
    }

    creados = 0
    for apartamento_id in activos:
        if apartamento_id in ya_tienen:
            continue
        db.add(
            Cargo(
                conjunto_id=conjunto_id,
                apartamento_id=apartamento_id,
                periodo=datos.periodo,
                concepto=datos.concepto,
                monto=datos.monto,
            )
        )
        if buscar_estado(db, apartamento_id) is None:
            db.add(EstadoApartamento(conjunto_id=conjunto_id, apartamento_id=apartamento_id))
        creados += 1

    db.flush()
    for apartamento_id in activos:
        estado = buscar_estado(db, apartamento_id)
        if estado is not None:
            actualizar_estado(db, estado)
    db.commit()
    return ResultadoMasivo(creados=creados, omitidos=len(activos) - creados)


@app.put(
    "/deudas/conjunto/{conjunto_id}/apartamentos/{apartamento_id}/gestion/",
    response_model=EstadoRespuesta,
)
def actualizar_gestion(
    conjunto_id: int,
    apartamento_id: int,
    datos: GestionActualizar,
    db: Session = Depends(get_db),
):
    try:
        apartamento = obtener_apartamento(apartamento_id)
    except ServicioNoDisponible:
        return JSONResponse(status_code=503, content={"error": "auth-service no está disponible."})
    if apartamento is None or apartamento["conjunto"] != conjunto_id:
        return JSONResponse(
            status_code=404,
            content={"error": "El apartamento no existe en este conjunto."},
        )

    estado = buscar_estado(db, apartamento_id)
    if estado is None:
        estado = EstadoApartamento(conjunto_id=conjunto_id, apartamento_id=apartamento_id)
        db.add(estado)
        db.flush()

    if datos.notas is not None:
        estado.notas = datos.notas
    if datos.acuerdo:
        estado.estado_gestion = ACUERDO
    elif estado.estado_gestion == ACUERDO:
        estado.estado_gestion = NORMAL
        actualizar_estado(db, estado)

    db.commit()
    db.refresh(estado)
    return respuesta_estado(db, estado)