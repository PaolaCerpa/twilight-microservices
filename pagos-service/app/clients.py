import httpx

from .config import AUTH_SERVICE_URL, DEUDAS_SERVICE_URL

TIMEOUT = 5.0

class ServicioNoDisponible(Exception):
    pass
def obtener_apartamento(apartamento_id: int) -> dict | None:
    url = f"{AUTH_SERVICE_URL}/auth/apartamento/{apartamento_id}/"
    try:
        response = httpx.get(url, timeout=TIMEOUT)
    except httpx.RequestError as e:
        raise ServicioNoDisponible("El servicio de autenticación no está disponible") from e

    if response.status_code == 200:
        return response.json()
    if response.status_code == 404:
        return None
        raise ServicioNoDisponible(f"Error al obtener el apartamento {apartamento_id}: {response.status_code}")

def aplicar_pago_en_deudas(apartamento_id: int, pago_id: int, monto) -> bool:
    url = f"{DEUDAS_SERVICE_URL}/deudas/{apartamento_id}/actualizar/"
    try:
        response = httpx.post(
                url, json={"pago_id": pago_id, "monto": str(monto)}, timeout=TIMEOUT
    )
        return response.status_code == 200
    except httpx.RequestError:
        return False

def revertir_pago_en_deudas(apartamento_id: int, pago_id: int, monto) -> bool:
    url = f"{DEUDAS_SERVICE_URL}/deudas/{apartamento_id}/revertir/"
    try:
        response = httpx.post(
            url, json={"pago_id": pago_id, "monto": str(monto)},timeout=TIMEOUT
        )
        return response.status_code == 200
    except httpx.RequestError:
        return False