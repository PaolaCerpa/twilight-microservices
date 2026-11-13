from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import ACUERDO, JURIDICO, NORMAL, PRE_JURIDICO, Cargo, EstadoApartamento

MESES_PRE_JURIDICO = 3
MESES_JURIDICO = 6
CENTAVOS = Decimal("0.01")


def total_cargos(db: Session, apartamento_id: int) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(Cargo.monto), 0))
        .filter(Cargo.apartamento_id == apartamento_id)
        .scalar()
    )
    return Decimal(str(total)).quantize(CENTAVOS)


def saldo(db: Session, estado: EstadoApartamento) -> Decimal:
    return total_cargos(db, estado.apartamento_id) - estado.total_pagado


def actualizar_estado(db: Session, estado: EstadoApartamento) -> None:
    if saldo(db, estado) <= 0:
        nuevo = NORMAL  
    elif estado.estado_gestion == ACUERDO:
        return  
    else:
        cargo_antiguo = (
            db.query(Cargo)
            .filter(Cargo.apartamento_id == estado.apartamento_id)
            .order_by(Cargo.periodo.asc())
            .first()
        )
        if cargo_antiguo is None:
            return
        hoy = datetime.now(timezone.utc).date()
        meses = (hoy.year - cargo_antiguo.periodo.year) * 12 + (
            hoy.month - cargo_antiguo.periodo.month
        )
        if meses >= MESES_JURIDICO:
            nuevo = JURIDICO
        elif meses >= MESES_PRE_JURIDICO:
            nuevo = PRE_JURIDICO
        else:
            nuevo = NORMAL

    if estado.estado_gestion != nuevo:
        estado.estado_gestion = nuevo