"""Service layer para departamentos (D-15, D-16)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.normalize import normalize_org_code
from app.db.models import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services import cost_centers_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalized_code(raw: str) -> str:
    norm = normalize_org_code(raw)
    if not norm:
        raise HTTPException(status_code=422, detail="code inválido após normalização")
    return norm


def _find_duplicate_code(
    db: Session, normalized: str, *, exclude_id: Optional[int] = None
) -> Optional[Department]:
    stmt = select(Department)
    if exclude_id is not None:
        stmt = stmt.where(Department.id != exclude_id)
    for row in db.scalars(stmt):
        existing = normalize_org_code(row.code)
        if existing == normalized:
            return row
    return None


def _validate_cost_center_id(db: Session, cost_center_id: Optional[int]) -> None:
    if cost_center_id is None:
        return
    cc = cost_centers_service.get_cost_center_by_id(db, cost_center_id)
    if cc is None:
        raise HTTPException(status_code=422, detail="cost_center_id não encontrado")
    if not cc.is_active:
        raise HTTPException(status_code=422, detail="cost_center_id inativo")


def list_departments(
    db: Session,
    *,
    include_inactive: bool = False,
    q: Optional[str] = None,
) -> list[Department]:
    stmt = select(Department).order_by(Department.name.asc())
    if not include_inactive:
        stmt = stmt.where(Department.is_active.is_(True))
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Department.code.ilike(term), Department.name.ilike(term))
        )
    return list(db.scalars(stmt))


def get_department_by_id(db: Session, department_id: int) -> Optional[Department]:
    return db.get(Department, department_id)


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    normalized = _normalized_code(payload.code)
    if _find_duplicate_code(db, normalized) is not None:
        raise HTTPException(status_code=409, detail="code já cadastrado")
    _validate_cost_center_id(db, payload.cost_center_id)

    now = _utc_now()
    row = Department(
        code=normalized,
        name=payload.name.strip(),
        cost_center_id=payload.cost_center_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_department(
    db: Session, department_id: int, payload: DepartmentUpdate
) -> Department:
    row = get_department_by_id(db, department_id)
    if row is None:
        raise HTTPException(status_code=404, detail="department not found")

    data = payload.model_dump(exclude_unset=True)
    if "code" in data and data["code"] is not None:
        normalized = _normalized_code(data["code"])
        dup = _find_duplicate_code(db, normalized, exclude_id=department_id)
        if dup is not None:
            raise HTTPException(status_code=409, detail="code já cadastrado")
        data["code"] = normalized
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    if "cost_center_id" in data:
        _validate_cost_center_id(db, data["cost_center_id"])

    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row


def soft_delete_department(db: Session, department_id: int) -> Department:
    row = get_department_by_id(db, department_id)
    if row is None:
        raise HTTPException(status_code=404, detail="department not found")
    row.is_active = False
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row
