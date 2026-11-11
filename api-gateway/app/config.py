import os

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
DEUDAS_SERVICE_URL = os.getenv("DEUDAS_SERVICE_URL", "http://127.0.0.1:8002")
PAGOS_SERVICE_URL = os.getenv("PAGOS_SERVICE_URL", "http://127.0.0.1:8003")
NOTIFICACIONES_SERVICE_URL = os.getenv("NOTIFICACIONES_SERVICE_URL", "http://127.0.0.1:8004")

# Clave temporal para las rutas de administración. Este valor por defecto
# es solo para desarrollo: en Docker se pasa por variable de entorno.
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "clave-solo-desarrollo")

TIMEOUT = float(os.getenv("GATEWAY_TIMEOUT", "10"))