from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .clients import ServicioNoDisponible, obtener_apartamento
from .database import Base, engine, get_db
from .models import Notificacion
from .schemas import NotificacionCrear, NotificacionRespuesta


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="notificaciones-service", lifespan=lifespan)


@app.post("/notificaciones", response_model=NotificacionRespuesta, status_code=201)
def crear_notificacion(datos: NotificacionCrear, db: Session = Depends(get_db)):
    conjunto_id = datos.conjunto_id

    if datos.apartamento_id is not None:
        try:
            apartamento = obtener_apartamento(datos.apartamento_id)
        except ServicioNoDisponible:
            raise HTTPException(status_code=503, detail="auth-service no está disponible.")
        if apartamento is None:
            raise HTTPException(status_code=404, detail="El apartamento no existe.")
        conjunto_id = apartamento["conjunto"]

    notificacion = Notificacion(
        conjunto_id=conjunto_id,
        apartamento_id=datos.apartamento_id,
        tipo=datos.tipo,
        mensaje=datos.mensaje,
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


@app.get("/notificaciones/apartamento/{apartamento_id}", response_model=list[NotificacionRespuesta])
def notificaciones_de_apartamento(
    apartamento_id: int, solo_no_leidas: bool = False, db: Session = Depends(get_db)
):
    consulta = db.query(Notificacion).filter(Notificacion.apartamento_id == apartamento_id)
    if solo_no_leidas:
        consulta = consulta.filter(Notificacion.leida.is_(False))
    return consulta.order_by(Notificacion.creado_en.desc()).all()


@app.get("/notificaciones/conjunto/{conjunto_id}/administracion", response_model=list[NotificacionRespuesta])
def notificaciones_de_administracion(
    conjunto_id: int, solo_no_leidas: bool = False, db: Session = Depends(get_db)
):
    consulta = db.query(Notificacion).filter(
        Notificacion.conjunto_id == conjunto_id,
        Notificacion.apartamento_id.is_(None),
    )
    if solo_no_leidas:
        consulta = consulta.filter(Notificacion.leida.is_(False))
    return consulta.order_by(Notificacion.creado_en.desc()).all()


@app.patch("/notificaciones/{notificacion_id}/leida", response_model=NotificacionRespuesta)
def marcar_leida(notificacion_id: int, db: Session = Depends(get_db)):
    notificacion = db.get(Notificacion, notificacion_id)
    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)
    return notificacion