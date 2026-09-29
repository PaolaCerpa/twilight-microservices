import requests
from django.conf import settings


def obtener_apartamento(apartamento_id):
    url = f"{settings.AUTH_SERVICE_URL}/auth/apartamento/{apartamento_id}/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None