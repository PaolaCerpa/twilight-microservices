from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Apartamento, Conjunto
from .schemas import (
    ApartamentoCrear,
    ApartamentoRespuesta,
    ConjuntoCrear,
    ConjuntoRespuesta,
    LoginCrear,
    LoginRespuesta,
)
from .security import (
    HASH_FALSO,
    decodificar_token,
    generar_token,
    hashear_password,
    verificar_password,
)

esquema_bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="auth-service", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def errores_de_validacion(request: Request, exc: RequestValidationError):
    """Mantiene el contrato de Django: 400 con {campo: [mensajes]}."""
    errores = {}
    for e in exc.errors():
        campo = str(e["loc"][-1]) if e["loc"] else "body"
        mensaje = "Este campo es requerido." if e["type"] == "missing" else e["msg"]
        errores.setdefault(campo, []).append(mensaje)
    return JSONResponse(status_code=400, content=errores)


# ---------- Contrato que consumen los demás servicios ----------

@app.post("/auth/login/", response_model=LoginRespuesta)
def login(datos: LoginCrear, db: Session = Depends(get_db)):
    apartamento = (
        db.query(Apartamento)
        .filter(
            Apartamento.conjunto_id == datos.conjunto,
            Apartamento.bloque == datos.bloque,
            Apartamento.apto == datos.apto,
            Apartamento.activo.is_(True),
        )
        .first()
    )
    # Siempre se verifica un hash, exista o no el apartamento (mismo tiempo de respuesta).
    guardado = apartamento.password if apartamento else HASH_FALSO
    valido = verificar_password(datos.password, guardado)

    if apartamento is None or not valido:
        return JSONResponse(status_code=401, content={"error": "Credenciales incorrectas."})

    return LoginRespuesta(
        token=generar_token(apartamento),
        apartamento=ApartamentoRespuesta.model_validate(apartamento),
    )


@app.get("/auth/validate/")
def validar_token(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
):
    if credenciales is None:
        return JSONResponse(
            status_code=401, content={"valid": False, "error": "Token no proporcionado"}
        )
    try:
        payload = decodificar_token(credenciales.credentials)
    except jwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"valid": False, "error": "Token expirado"})
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"valid": False, "error": "Token inválido"})
    return {"valid": True, "payload": payload}


@app.get("/auth/apartamento/{apartamento_id}/", response_model=ApartamentoRespuesta)
def detalle_apartamento(apartamento_id: int, db: Session = Depends(get_db)):
    apartamento = db.get(Apartamento, apartamento_id)
    if apartamento is None:
        return JSONResponse(status_code=404, content={"error": "Apartamento no encontrado."})
    return apartamento


# ---------- Administración (reemplaza el admin de Django) ----------
# Estas rutas no validan quién llama: solo deben alcanzarse a través del gateway.

@app.post("/auth/conjuntos/", response_model=ConjuntoRespuesta, status_code=201)
def crear_conjunto(datos: ConjuntoCrear, db: Session = Depends(get_db)):
    conjunto = Conjunto(**datos.model_dump())
    db.add(conjunto)
    db.commit()
    db.refresh(conjunto)
    return conjunto


@app.get("/auth/conjuntos/", response_model=list[ConjuntoRespuesta])
def listar_conjuntos(db: Session = Depends(get_db)):
    return db.query(Conjunto).order_by(Conjunto.id).all()


@app.post("/auth/apartamentos/", response_model=ApartamentoRespuesta, status_code=201)
def crear_apartamento(datos: ApartamentoCrear, db: Session = Depends(get_db)):
    if db.get(Conjunto, datos.conjunto) is None:
        return JSONResponse(status_code=404, content={"error": "El conjunto no existe."})

    apartamento = Apartamento(
        conjunto_id=datos.conjunto,
        bloque=datos.bloque,
        apto=datos.apto,
        propietario=datos.propietario,
        telefono=datos.telefono,
        email=datos.email,
        password=hashear_password(datos.password),
    )
    db.add(apartamento)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=409,
            content={"error": "Ya existe ese bloque y apartamento en el conjunto."},
        )
    db.refresh(apartamento)
    return apartamento