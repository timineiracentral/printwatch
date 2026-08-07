"""Claims de envio bem-sucedido por invoice×stage×contact×part (CAD-03, D-12)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.simpress.db.models import SendClaim


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def record_success(
    db: Session,
    *,
    invoice_id: int,
    stage: str,
    contact_id: int,
    part: str,
    provider_message_id: str | None = None,
) -> None:
    row = SendClaim(
        invoice_id=invoice_id,
        stage=stage,
        contact_id=contact_id,
        part=part,
        provider_message_id=provider_message_id,
        created_at=_utc_now(),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def has_claim(
    db: Session,
    *,
    invoice_id: int,
    stage: str,
    contact_id: int,
    part: str,
) -> bool:
    row = db.scalars(
        select(SendClaim.id).where(
            SendClaim.invoice_id == invoice_id,
            SendClaim.stage == stage,
            SendClaim.contact_id == contact_id,
            SendClaim.part == part,
        )
    ).first()
    return row is not None


def count_claims(
    db: Session,
    *,
    invoice_id: int,
    stage: str | None = None,
    contact_id: int | None = None,
    part: str | None = None,
) -> int:
    stmt = select(func.count()).select_from(SendClaim).where(
        SendClaim.invoice_id == invoice_id
    )
    if stage is not None:
        stmt = stmt.where(SendClaim.stage == stage)
    if contact_id is not None:
        stmt = stmt.where(SendClaim.contact_id == contact_id)
    if part is not None:
        stmt = stmt.where(SendClaim.part == part)
    return int(db.scalar(stmt) or 0)
