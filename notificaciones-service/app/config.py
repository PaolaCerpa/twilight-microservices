import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notificaciones.db")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")