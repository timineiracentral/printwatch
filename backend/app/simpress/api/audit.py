"""API listagem append-only de audit (OPS-02, D-16..D-19)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.simpress.db.session import get_simpress_db
from app.simpress.schemas.audit import MessageAuditRead
from app.simpress.services import audit_service

router = APIRouter()


@router.get("", response_model=list[MessageAuditRead])
def list_audit(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_simpress_db),
) -> list[MessageAuditRead]:
    return audit_service.list_audit(db, limit=limit)
