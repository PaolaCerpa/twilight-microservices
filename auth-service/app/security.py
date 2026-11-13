import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import JWT_EXPIRACION_HORAS, JWT_SECRET

ALGORITMO_JWT = "HS256"
ITERACIONES = 600_000


def hashear_password(password: str) -> str:
    sal = secrets.token_hex(16)
    resumen = hashlib.pbkdf2_hmac("sha256", password.encode(), sal.encode(), ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal}${resumen.hex()}"


def verificar_password(password: str, guardado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, resumen = guardado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        calculado = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), sal.encode(), int(iteraciones)
        )
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(calculado.hex(), resumen)


HASH_FALSO = hashear_password("relleno")


def generar_token(apartamento) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "apartamento_id": apartamento.id,
        "bloque": apartamento.bloque,
        "apto": apartamento.apto,
        "exp": ahora + timedelta(hours=JWT_EXPIRACION_HORAS),
        "iat": ahora,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITMO_JWT)


def decodificar_token(token: str) -> dict:
    """Lanza jwt.ExpiredSignatureError o jwt.InvalidTokenError si el token no sirve."""
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITMO_JWT])