import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

ENTORNO = os.getenv("APP_ENV", "desarrollo")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-clave-insegura-no-usar-en-produccion")
JWT_EXPIRACION_HORAS = int(os.getenv("JWT_EXPIRACION_HORAS", "24"))

if ENTORNO == "produccion" and JWT_SECRET == "dev-only-clave-insegura-no-usar-en-produccion":
        raise RuntimeError("Define JWT_SECRET en el entorno de producción.")