from fastapi import APIRouter, Body, Depends

from .config import AUTH_SERVICE_URL
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