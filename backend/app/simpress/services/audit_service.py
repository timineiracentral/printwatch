"""Audit append-only de tentativas WhatsApp (OPS-02, D-17/D-18)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.simpress.db.models import MessageAudit


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def append_audit(
    db: Session,
    *,
    channel: str,
    part: str,
    stage: str,
    outcome: str,
    contact_id: int | None = None,
    contact_name: str | None = None,
    contact_phone: str | None = None,
    http_status: int | None = None,
    provider_message_id: str | None = None,
    variant_id: str | None = None,
) -> MessageAudit:
    row = MessageAudit(
        channel=channel,
        part=part,
        stage=stage,
        outcome=outcome,
        contact_id=contact_id,
        contact_name=contact_name,
        contact_phone=contact_phone,
        http_status=http_status,
        provider_message_id=provider_message_id,
        variant_id=variant_id,
        created_at=_utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_audit(db: Session, limit: int = 100) -> list[MessageAudit]:
    cap = max(1, min(limit, 500))
    return list(
        db.scalars(
            select(MessageAudit).order_by(MessageAudit.created_at.desc()).limit(cap)
        )
    )
