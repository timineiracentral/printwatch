"""Service layer para centros de custo (D-15, D-16)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.normalize import normalize_org_code
from app.db.models import CostCenter
from app.schemas.cost_center import CostCenterCreate, CostCenterUpdate


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalized_code(raw: str) -> str:
    norm = normalize_org_code(raw)
    if not norm:
        raise HTTPException(status_code=422, detail="code inválido após normalização")
    return norm


def _find_duplicate_code(
    db: Session, normalized: str, *, exclude_id: Optional[int] = None
) -> Optional[CostCenter]:
    stmt = select(CostCenter)
    if exclude_id is not None:
        stmt = stmt.where(CostCenter.id != exclude_id)
    for row in db.scalars(stmt):
        existing = normalize_org_code(row.code)
        if existing == normalized:
            return row
    return None


def list_cost_centers(
    db: Session,
    *,
    include_inactive: bool = False,
    q: Optional[str] = None,
) -> list[CostCenter]:
    stmt = select(CostCenter).order_by(CostCenter.name.asc())
    if not include_inactive:
        stmt = stmt.where(CostCenter.is_active.is_(True))
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(CostCenter.code.ilike(term), CostCenter.name.ilike(term))
        )
    return list(db.scalars(stmt))


def get_cost_center_by_id(db: Session, cost_center_id: int) -> Optional[CostCenter]:
    return db.get(CostCenter, cost_center_id)


def create_cost_center(db: Session, payload: CostCenterCreate) -> CostCenter:
    normalized = _normalized_code(payload.code)
    if _find_duplicate_code(db, normalized) is not None:
        raise HTTPException(status_code=409, detail="code já cadastrado")

    now = _utc_now()
    row = CostCenter(
        code=normalized,
        name=payload.name.strip(),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_cost_center(
    db: Session, cost_center_id: int, payload: CostCenterUpdate
) -> CostCenter:
    row = get_cost_center_by_id(db, cost_center_id)
    if row is None:
        raise HTTPException(status_code=404, detail="cost center not found")

    data = payload.model_dump(exclude_unset=True)
    if "code" in data and data["code"] is not None:
        normalized = _normalized_code(data["code"])
        dup = _find_duplicate_code(db, normalized, exclude_id=cost_center_id)
        if dup is not None:
            raise HTTPException(status_code=409, detail="code já cadastrado")
        data["code"] = normalized
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()

    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row


def soft_delete_cost_center(db: Session, cost_center_id: int) -> CostCenter:
    row = get_cost_center_by_id(db, cost_center_id)
    if row is None:
        raise HTTPException(status_code=404, detail="cost center not found")
    row.is_active = False
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row
