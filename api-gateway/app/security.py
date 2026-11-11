import secrets

import httpx
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import ADMIN_API_KEY, AUTH_SERVICE_URL, TIMEOUT

esquema_bearer = HTTPBearer(auto_error=False)


async def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
) -> dict:
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Token no proporcionado.")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            respuesta = await client.get(
                f"{AUTH_SERVICE_URL}/auth/validate/",
                headers={"Authorization": f"Bearer {credenciales.credentials}"},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="auth-service no está disponible.")

    if respuesta.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    return respuesta.json()["payload"]


def exigir_propio(apartamento_id: int, usuario: dict) -> None:
    if usuario["apartamento_id"] != apartamento_id:
        raise HTTPException(
            status_code=403,
            detail="No puedes acceder a información de otro apartamento.",
        )


def exigir_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if not x_admin_key or not secrets.compare_digest(
        x_admin_key.encode(), ADMIN_API_KEY.encode()
    ):
        raise HTTPException(status_code=403, detail="Se requiere clave de administración.")