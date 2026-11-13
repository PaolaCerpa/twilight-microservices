from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    AUTH_SERVICE_URL,
    DEUDAS_SERVICE_URL,
    NOTIFICACIONES_SERVICE_URL,
    PAGOS_SERVICE_URL,
)
from .proxy import reenviar
from .security import exigir_admin, exigir_propio, usuario_actual

app = FastAPI(title="api-gateway")

# Solo para desarrollo: permite que la app web de Flutter (Chrome) llame al gateway.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"estado": "ok"}


# ---------- Autenticación (pública) ----------

@app.post("/api/auth/login")
async def login(datos: dict = Body(...)):
    return await reenviar("POST", f"{AUTH_SERVICE_URL}/auth/login/", json=datos)


# ---------- Residente: solo su propio apartamento ----------

@app.get("/api/deudas/{apartamento_id}")
async def deuda_actual(apartamento_id: int, usuario: dict = Depends(usuario_actual)):
    exigir_propio(apartamento_id, usuario)
    return await reenviar("GET", f"{DEUDAS_SERVICE_URL}/deudas/{apartamento_id}/")


@app.get("/api/deudas/{apartamento_id}/historial")
async def historial_deuda(apartamento_id: int, usuario: dict = Depends(usuario_actual)):
    exigir_propio(apartamento_id, usuario)
    return await reenviar("GET", f"{DEUDAS_SERVICE_URL}/deudas/{apartamento_id}/historial/")


@app.get("/api/pagos/{apartamento_id}")
async def historial_pagos(
    apartamento_id: int,
    estado: str | None = None,
    usuario: dict = Depends(usuario_actual),
):
    exigir_propio(apartamento_id, usuario)
    params = {"estado": estado} if estado else None
    return await reenviar("GET", f"{PAGOS_SERVICE_URL}/pagos/{apartamento_id}", params=params)


@app.post("/api/pagos")
async def registrar_pago(datos: dict = Body(...), usuario: dict = Depends(usuario_actual)):
    try:
        apartamento_id = int(datos.get("apartamento_id"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422, detail="apartamento_id es requerido y debe ser un número."
        )
    exigir_propio(apartamento_id, usuario)
    return await reenviar("POST", f"{PAGOS_SERVICE_URL}/pagos", json=datos)


@app.get("/api/notificaciones/apartamento/{apartamento_id}")
async def notificaciones_residente(
    apartamento_id: int,
    solo_no_leidas: bool = False,
    usuario: dict = Depends(usuario_actual),
):
    exigir_propio(apartamento_id, usuario)
    return await reenviar(
        "GET",
        f"{NOTIFICACIONES_SERVICE_URL}/notificaciones/apartamento/{apartamento_id}",
        params={"solo_no_leidas": solo_no_leidas},
    )


# ---------- Administración: exigen X-Admin-Key ----------

@app.post("/api/admin/cargos", dependencies=[Depends(exigir_admin)])
async def crear_cargo(datos: dict = Body(...)):
    return await reenviar("POST", f"{DEUDAS_SERVICE_URL}/deudas/cargos/", json=datos)


@app.post("/api/admin/pagos/{pago_id}/anular", dependencies=[Depends(exigir_admin)])
async def anular_pago(pago_id: int):
    return await reenviar("POST", f"{PAGOS_SERVICE_URL}/pagos/{pago_id}/anular")


@app.get(
    "/api/admin/conjuntos/{conjunto_id}/notificaciones",
    dependencies=[Depends(exigir_admin)],
)
async def notificaciones_administracion(conjunto_id: int, solo_no_leidas: bool = False):
    return await reenviar(
        "GET",
        f"{NOTIFICACIONES_SERVICE_URL}/notificaciones/conjunto/{conjunto_id}/administracion",
        params={"solo_no_leidas": solo_no_leidas},
    )

@app.post("/api/admin/conjuntos", dependencies=[Depends(exigir_admin)])
async def crear_conjunto(datos: dict = Body(...)):
    return await reenviar("POST", f"{AUTH_SERVICE_URL}/auth/conjuntos/", json=datos)


@app.get("/api/admin/conjuntos", dependencies=[Depends(exigir_admin)])
async def listar_conjuntos():
    return await reenviar("GET", f"{AUTH_SERVICE_URL}/auth/conjuntos/")


@app.post("/api/admin/apartamentos", dependencies=[Depends(exigir_admin)])
async def crear_apartamento(datos: dict = Body(...)):
    return await reenviar("POST", f"{AUTH_SERVICE_URL}/auth/apartamentos/", json=datos)