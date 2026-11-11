import httpx
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from .config import TIMEOUT


async def reenviar(metodo: str, url: str, *, json=None, params=None) -> JSONResponse:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            respuesta = await client.request(metodo, url, json=json, params=params)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="El servicio tardó demasiado en responder.")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="El servicio no está disponible.")

    try:
        contenido = respuesta.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Respuesta inválida del servicio interno.")

    return JSONResponse(status_code=respuesta.status_code, content=contenido)