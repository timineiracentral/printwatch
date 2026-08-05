"""Service layer CNPJs Simpress (CNPJ-01, D-09..D-12)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.simpress.db.models import Cnpj, CnpjContact
from app.simpress.schemas.cnpj import CnpjCreate, CnpjUpdate


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def list_cnpjs(
    db: Session,
    *,
    include_inactive: bool = False,
    q: Optional[str] = None,
) -> list[Cnpj]:
    stmt = select(Cnpj).order_by(Cnpj.name.asc())
    if not include_inactive:
        stmt = stmt.where(Cnpj.is_active.is_(True))
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(Cnpj.cnpj.ilike(term), Cnpj.name.ilike(term)))
    return list(db.scalars(stmt))


def get_cnpj_by_id(db: Session, cnpj_id: int) -> Optional[Cnpj]:
    return db.get(Cnpj, cnpj_id)


def _find_duplicate_cnpj(
    db: Session, normalized: str, *, exclude_id: Optional[int] = None
) -> Optional[Cnpj]:
    stmt = select(Cnpj).where(Cnpj.cnpj == normalized)
    if exclude_id is not None:
        stmt = stmt.where(Cnpj.id != exclude_id)
    return db.scalars(stmt).first()


def create_cnpj(db: Session, payload: CnpjCreate) -> Cnpj:
    existing = _find_duplicate_cnpj(db, payload.cnpj)
    if existing is not None:
        if existing.is_active:
            raise HTTPException(status_code=409, detail="cnpj já cadastrado")
        now = _utc_now()
        existing.name = payload.name
        existing.is_active = True
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        return existing

    now = _utc_now()
    row = Cnpj(
        cnpj=payload.cnpj,
        name=payload.name,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_cnpj(db: Session, cnpj_id: int, payload: CnpjUpdate) -> Cnpj:
    row = get_cnpj_by_id(db, cnpj_id)
    if row is None:
        raise HTTPException(status_code=404, detail="cnpj not found")

    data = payload.model_dump(exclude_unset=True)
    if "cnpj" in data and data["cnpj"] is not None:
        dup = _find_duplicate_cnpj(db, data["cnpj"], exclude_id=cnpj_id)
        if dup is not None:
            raise HTTPException(status_code=409, detail="cnpj já cadastrado")

    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row


def soft_delete_cnpj(db: Session, cnpj_id: int) -> Cnpj:
    row = get_cnpj_by_id(db, cnpj_id)
    if row is None:
        raise HTTPException(status_code=404, detail="cnpj not found")

    now = _utc_now()
    row.is_active = False
    row.updated_at = now

    for link in db.scalars(
        select(CnpjContact).where(CnpjContact.cnpj_id == cnpj_id)
    ):
        link.is_active = False
        link.updated_at = now

    db.commit()
    db.refresh(row)
    return row
