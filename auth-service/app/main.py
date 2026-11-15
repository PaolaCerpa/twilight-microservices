from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Administrador, Apartamento, Conjunto
from .schemas import (
    AdminLoginCrear,
    AdminLoginRespuesta,
    AdministradorCrear,
    AdministradorRespuesta,
    ApartamentoCrear,
    ApartamentoActualizar,
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
    generar_token_admin,
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
    errores = {}
    for e in exc.errors():
        campo = str(e["loc"][-1]) if e["loc"] else "body"
        mensaje = "Este campo es requerido." if e["type"] == "missing" else e["msg"]
        errores.setdefault(campo, []).append(mensaje)
    return JSONResponse(status_code=400, content=errores)


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


@app.post("/auth/admin/login/", response_model=AdminLoginRespuesta)
def login_admin(datos: AdminLoginCrear, db: Session = Depends(get_db)):
    administrador = (
        db.query(Administrador)
        .filter(
            Administrador.usuario == datos.usuario.strip().lower(),
            Administrador.activo.is_(True),
        )
        .first()
    )
    guardado = administrador.password if administrador else HASH_FALSO
    valido = verificar_password(datos.password, guardado)

    if administrador is None or not valido:
        return JSONResponse(status_code=401, content={"error": "Credenciales incorrectas."})

    return AdminLoginRespuesta(
        token=generar_token_admin(administrador),
        administrador=AdministradorRespuesta.model_validate(administrador),
    )


@app.post("/auth/administradores/", response_model=AdministradorRespuesta, status_code=201)
def crear_administrador(datos: AdministradorCrear, db: Session = Depends(get_db)):
    if db.get(Conjunto, datos.conjunto) is None:
        return JSONResponse(status_code=404, content={"error": "El conjunto no existe."})

    administrador = Administrador(
        conjunto_id=datos.conjunto,
        usuario=datos.usuario.strip().lower(),
        nombre=datos.nombre,
        password=hashear_password(datos.password),
    )
    db.add(administrador)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=409,
            content={"error": "Ya existe un administrador con ese usuario."},
        )
    db.refresh(administrador)
    return administrador


@app.get("/auth/conjuntos/{conjunto_id}/", response_model=ConjuntoRespuesta)
def detalle_conjunto(conjunto_id: int, db: Session = Depends(get_db)):
    conjunto = db.get(Conjunto, conjunto_id)
    if conjunto is None:
        return JSONResponse(status_code=404, content={"error": "El conjunto no existe."})
    return conjunto


@app.get(
    "/auth/conjuntos/{conjunto_id}/apartamentos/",
    response_model=list[ApartamentoRespuesta],
)
def apartamentos_del_conjunto(conjunto_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Apartamento)
        .filter(Apartamento.conjunto_id == conjunto_id)
        .order_by(Apartamento.bloque, Apartamento.apto)
        .all()
    )


@app.patch(
    "/auth/conjuntos/{conjunto_id}/apartamentos/{apartamento_id}/",
    response_model=ApartamentoRespuesta,
)
def actualizar_apartamento(
    conjunto_id: int,
    apartamento_id: int,
    datos: ApartamentoActualizar,
    db: Session = Depends(get_db),
):
    apartamento = (
        db.query(Apartamento)
        .filter(Apartamento.id == apartamento_id, Apartamento.conjunto_id == conjunto_id)
        .first()
    )
    if apartamento is None:
        return JSONResponse(status_code=404, content={"error": "Apartamento no encontrado."})

    cambios = datos.model_dump(exclude_unset=True)
    nueva_password = cambios.pop("password", None)
    for campo, valor in cambios.items():
        if valor is not None:
            setattr(apartamento, campo, valor)
    if nueva_password:
        apartamento.password = hashear_password(nueva_password)

    db.commit()
    db.refresh(apartamento)
    return apartamento