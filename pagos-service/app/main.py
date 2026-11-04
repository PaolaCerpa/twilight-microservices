import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .clients import (
    ServicioNoDisponible,
    aplicar_pago_en_deudas,
    obtener_apartamento,
    revertir_pago_en_deudas,
)
from .config import INTERVALO_OUTBOX, MAX_INTENTOS
from .database import Base, SessionLocal, engine, get_db
from .models import ANULADO, CONFIRMADO, FALLIDO, Outbox, Pago, ahora_utc
from .schemas import PagoCrear, PagoRespuesta

EVENTO_REGISTRADO = "PAGO_REGISTRADO"
EVENTO_ANULADO = "PAGO_ANULADO"

_lock = threading.Lock() 


def procesar_outbox() -> int:
    resueltos = 0
    with _lock:
        db = SessionLocal()
        try:
            eventos = (
                db.query(Outbox)
                .filter(Outbox.procesado.is_(False))
                .order_by(Outbox.id)
                .all()
            )
            for evento in eventos:
                pago = db.get(Pago, evento.pago_id)
                datos = evento.payload

                if evento.tipo == EVENTO_REGISTRADO:
                    if aplicar_pago_en_deudas(datos["apartamento_id"], pago.id, datos["monto"]):
                        pago.estado = CONFIRMADO
                        evento.procesado = True
                    else:
                        evento.intentos += 1
                        if evento.intentos >= MAX_INTENTOS:
                            pago.estado = FALLIDO
                            evento.procesado = True

                elif evento.tipo == EVENTO_ANULADO:
                    if revertir_pago_en_deudas(datos["apartamento_id"], pago.id, datos["monto"]):
                        evento.procesado = True
                    else:
                        evento.intentos += 1

                if evento.procesado:
                    evento.procesado_en = ahora_utc()
                    resueltos += 1
                db.commit()
        finally:
            db.close()
    return resueltos


async def worker_outbox():
    while True:
        try:
            await asyncio.to_thread(procesar_outbox)
        except Exception as e:
            print(f"[outbox] Error al procesar outbox: {e}")
        await asyncio.sleep(INTERVALO_OUTBOX)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    tarea = asyncio.create_task(worker_outbox())
    yield
    tarea.cancel()


app = FastAPI(title="pagos-service", lifespan=lifespan)


@app.post("/pagos", response_model=PagoRespuesta, status_code=201)
def registrar_pago(datos: PagoCrear, db: Session = Depends(get_db)):
    try:
        apartamento = obtener_apartamento(datos.apartamento_id)
    except ServicioNoDisponible:
        raise HTTPException(status_code=503, detail="Servicio de apartamentos no disponible.")
    if apartamento is None:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado.")

    pago = Pago(conjunto_id=apartamento["conjunto"], **datos.model_dump())
    db.add(pago)
    db.flush()
    db.add(Outbox(
           pago_id=pago.id,
           tipo=EVENTO_REGISTRADO,
           payload={"apartamento_id": pago.apartamento_id, "monto": str(pago.monto)},
    ))
    db.commit()

    procesar_outbox()
    db.refresh(pago)
    return pago


@app.get("/pagos/{apartamento_id}", response_model=list[PagoRespuesta])
def historial_pagos(apartamento_id: int, estado: str | None = None, db: Session = Depends(get_db)):
    consulta = db.query(Pago).filter(Pago.apartamento_id == apartamento_id)
    if estado:
        consulta = consulta.filter(Pago.estado == estado)
    return consulta.order_by(Pago.fecha.desc()).all()


@app.post("/pagos/{pago_id}/anular", response_model=PagoRespuesta)
def anular_pago(pago_id: int, db: Session = Depends(get_db)):
    pago = db.get(Pago, pago_id)
    if pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    if pago.estado != CONFIRMADO:
        raise HTTPException(status_code=409, detail=f"Solo se pueden anular pagos confirmados. Estado actual: {pago.estado}.")

    pago.estado = ANULADO
    db.add(Outbox(
        pago_id=pago.id,
        tipo=EVENTO_ANULADO,
        payload={"apartamento_id": pago.apartamento_id, "monto": str(pago.monto)},
    ))
    db.commit()

    procesar_outbox()
    db.refresh(pago)
    return pago


@app.post("/outbox/procesar")
def forzar_outbox():
    return {"resueltos": procesar_outbox()}