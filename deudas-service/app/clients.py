import httpx

from .config import AUTH_SERVICE_URL

TIMEOUT = 5.0


class ServicioNoDisponible(Exception):
    pass


def obtener_apartamento(apartamento_id: int) -> dict | None:
    url = f"{AUTH_SERVICE_URL}/auth/apartamento/{apartamento_id}/"
    try:
        response = httpx.get(url, timeout=TIMEOUT)
    except httpx.RequestError as e:
        raise ServicioNoDisponible("auth-service no responde") from e

    if response.status_code == 200:
        return response.json()
    if response.status_code == 404:
        return None
    raise ServicioNoDisponible(f"auth-service respondió {response.status_code}")