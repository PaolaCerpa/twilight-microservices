from fastapi import APIRouter, Body, Depends

from .config import (
    AUTH_SERVICE_URL,
    DEUDAS_SERVICE_URL,
    NOTIFICACIONES_SERVICE_URL,
    PAGOS_SERVICE_URL,
)
from .proxy import reenviar
from .security import admin_actual

router = APIRouter(prefix="/api/admin", tags=["administración"])


@router.post("/login")
async def login_admin(datos: dict = Body(...)):
    return await reenviar("POST", f"{AUTH_SERVICE_URL}/auth/admin/login/", json=datos)


@router.get("/conjunto")
async def mi_conjunto(admin: dict = Depends(admin_actual)):
    return await reenviar("GET", f"{AUTH_SERVICE_URL}/auth/conjuntos/{admin['conjunto_id']}/")


@router.get("/apartamentos")
async def listar_apartamentos(admin: dict = Depends(admin_actual)):
    return await reenviar(
        "GET", f"{AUTH_SERVICE_URL}/auth/conjuntos/{admin['conjunto_id']}/apartamentos/"
    )


@router.post("/apartamentos")
async def crear_apartamento(datos: dict = Body(...), admin: dict = Depends(admin_actual)):
    datos["conjunto"] = admin["conjunto_id"] 
    return await reenviar("POST", f"{AUTH_SERVICE_URL}/auth/apartamentos/", json=datos)


@router.patch("/apartamentos/{apartamento_id}")
async def editar_apartamento(
    apartamento_id: int, datos: dict = Body(...), admin: dict = Depends(admin_actual)
):
    return await reenviar(
        "PATCH",
        f"{AUTH_SERVICE_URL}/auth/conjuntos/{admin['conjunto_id']}/apartamentos/{apartamento_id}/",
        json=datos,
    )


# ---------- Deudas y cuotas ----------

@router.get("/resumen")
async def resumen(admin: dict = Depends(admin_actual)):
    return await reenviar(
        "GET", f"{DEUDAS_SERVICE_URL}/deudas/conjunto/{admin['conjunto_id']}/resumen/"
    )


@router.get("/deudas")
async def reporte_deudas(admin: dict = Depends(admin_actual)):
    return await reenviar("GET", f"{DEUDAS_SERVICE_URL}/deudas/conjunto/{admin['conjunto_id']}/")


@router.put("/apartamentos/{apartamento_id}/gestion")
async def actualizar_gestion(
    apartamento_id: int, datos: dict = Body(...), admin: dict = Depends(admin_actual)
):
    return await reenviar(
        "PUT",
        f"{DEUDAS_SERVICE_URL}/deudas/conjunto/{admin['conjunto_id']}"
        f"/apartamentos/{apartamento_id}/gestion/",
        json=datos,
    )


@router.get("/cuotas")
async def listar_cuotas(admin: dict = Depends(admin_actual)):
    return await reenviar(
        "GET", f"{DEUDAS_SERVICE_URL}/deudas/conjunto/{admin['conjunto_id']}/cargos/",
    )


@router.post("/cuotas")
async def crear_cuota(datos: dict = Body(...), admin: dict = Depends(admin_actual)):
    return await reenviar(
        "POST",
        f"{DEUDAS_SERVICE_URL}/deudas/conjunto/{admin['conjunto_id']}/cargos/",
        json=datos,
    )


@router.post("/cuotas/masivo")
async def generar_cuotas(datos: dict = Body(...), admin: dict = Depends(admin_actual)):
    return await reenviar(
        "POST",
        f"{DEUDAS_SERVICE_URL}/deudas/conjunto/{admin['conjunto_id']}/cargos/masivo/",
        json=datos,
    )


@router.delete("/cuotas/{cargo_id}")
async def eliminar_cuota(cargo_id: int, admin: dict = Depends(admin_actual)):
    return await reenviar(
        "DELETE",
        f"{DEUDAS_SERVICE_URL}/deudas/conjunto/{admin['conjunto_id']}/cargos/{cargo_id}/",
    )


# ---------- Pagos ----------

@router.get("/pagos")
async def listar_pagos(estado: str | None = None, admin: dict = Depends(admin_actual)):
    
    params = {"estado": estado} if estado else None
    return await reenviar(
        "GET", f"{PAGOS_SERVICE_URL}/pagos/conjunto/{admin['conjunto_id']}", params=params
    )


@router.post("/pagos")
async def registrar_pago(datos: dict = Body(...), admin: dict = Depends(admin_actual)):
    return await reenviar(
        "POST",
        f"{PAGOS_SERVICE_URL}/pagos/conjunto/{admin['conjunto_id']}",
        json=datos,
    )


@router.post("/pagos/{pago_id}/anular")
async def anular_pago(pago_id: int, admin: dict = Depends(admin_actual)):
    return await reenviar(
        "POST",
        f"{PAGOS_SERVICE_URL}/pagos/conjunto/{admin['conjunto_id']}/{pago_id}/anular",
    )


# ---------- Avisos de la administración ----------

@router.get("/notificaciones")
async def listar_notificaciones(
    solo_no_leidas: bool = False, admin: dict = Depends(admin_actual)
):
    return await reenviar(
        "GET",
        f"{NOTIFICACIONES_SERVICE_URL}/notificaciones/conjunto/{admin['conjunto_id']}/administracion",
        params={"solo_no_leidas": solo_no_leidas},
    )


@router.patch("/notificaciones/{notificacion_id}/leida")
async def marcar_leida(notificacion_id: int, admin: dict = Depends(admin_actual)):
    return await reenviar(
        "PATCH",
        f"{NOTIFICACIONES_SERVICE_URL}/notificaciones/conjunto/{admin['conjunto_id']}"
        f"/administracion/{notificacion_id}/leida",
    )