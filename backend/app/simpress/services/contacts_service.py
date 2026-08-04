"""Service layer contatos Simpress (CNPJ-02, D-15..D-19)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.simpress.db.models import CnpjContact, Contact
from app.simpress.schemas.contact import ContactCreate, ContactUpdate


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def list_contacts(
    db: Session,
    *,
    include_inactive: bool = False,
    q: Optional[str] = None,
) -> list[Contact]:
    stmt = select(Contact).order_by(Contact.name.asc())
    if not include_inactive:
        stmt = stmt.where(Contact.is_active.is_(True))
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(Contact.name.ilike(term), Contact.phone.ilike(term)))
    return list(db.scalars(stmt))


def get_contact_by_id(db: Session, contact_id: int) -> Optional[Contact]:
    return db.get(Contact, contact_id)


def create_contact(db: Session, payload: ContactCreate) -> Contact:
    now = _utc_now()
    row = Contact(
        name=payload.name,
        phone=payload.phone,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_contact(
    db: Session, contact_id: int, payload: ContactUpdate
) -> Contact:
    row = get_contact_by_id(db, contact_id)
    if row is None:
        raise HTTPException(status_code=404, detail="contact not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row


def soft_delete_contact(db: Session, contact_id: int) -> Contact:
    row = get_contact_by_id(db, contact_id)
    if row is None:
        raise HTTPException(status_code=404, detail="contact not found")

    now = _utc_now()
    row.is_active = False
    row.updated_at = now

    for link in db.scalars(
        select(CnpjContact).where(CnpjContact.contact_id == contact_id)
    ):
        link.is_active = False
        link.updated_at = now

    db.commit()
    db.refresh(row)
    return row
