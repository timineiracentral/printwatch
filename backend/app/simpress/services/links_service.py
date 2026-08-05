"""N:N CNPJ ↔ contato — replace-style links (D-13, D-14)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.simpress.db.models import Cnpj, CnpjContact, Contact
from app.simpress.schemas.cnpj import ContactIdsReplace
from app.simpress.schemas.contact import CnpjIdsReplace, ContactRead
from app.simpress.schemas.cnpj import CnpjRead


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_cnpj_or_404(db: Session, cnpj_id: int) -> Cnpj:
    row = db.get(Cnpj, cnpj_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=404, detail="cnpj not found")
    return row


def _get_contact_or_404(db: Session, contact_id: int) -> Contact:
    row = db.get(Contact, contact_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=404, detail="contact not found")
    return row


def _validate_contact_ids(db: Session, contact_ids: list[int]) -> None:
    seen: set[int] = set()
    for cid in contact_ids:
        if cid in seen:
            raise HTTPException(
                status_code=422, detail="duplicate contact_id in contact_ids"
            )
        seen.add(cid)
        contact = _get_contact_or_404(db, cid)
        if not contact.is_active:
            raise HTTPException(
                status_code=404, detail=f"contact {cid} not found"
            )


def _validate_cnpj_ids(db: Session, cnpj_ids: list[int]) -> None:
    seen: set[int] = set()
    for cid in cnpj_ids:
        if cid in seen:
            raise HTTPException(
                status_code=422, detail="duplicate cnpj_id in cnpj_ids"
            )
        seen.add(cid)
        cnpj = _get_cnpj_or_404(db, cid)
        if not cnpj.is_active:
            raise HTTPException(status_code=404, detail=f"cnpj {cid} not found")


def list_contacts_for_cnpj(
    db: Session, cnpj_id: int, *, include_inactive: bool = False
) -> list[ContactRead]:
    _get_cnpj_or_404(db, cnpj_id)
    stmt = (
        select(Contact)
        .join(CnpjContact, CnpjContact.contact_id == Contact.id)
        .where(CnpjContact.cnpj_id == cnpj_id)
        .order_by(Contact.name.asc())
    )
    if not include_inactive:
        stmt = stmt.where(
            CnpjContact.is_active.is_(True),
            Contact.is_active.is_(True),
        )
    return [ContactRead.model_validate(c) for c in db.scalars(stmt)]


def replace_contacts_for_cnpj(
    db: Session, cnpj_id: int, payload: ContactIdsReplace
) -> list[ContactRead]:
    _get_cnpj_or_404(db, cnpj_id)
    _validate_contact_ids(db, payload.contact_ids)

    now = _utc_now()
    payload_ids = set(payload.contact_ids)

    existing = list(
        db.scalars(
            select(CnpjContact).where(CnpjContact.cnpj_id == cnpj_id)
        )
    )
    existing_by_contact = {r.contact_id: r for r in existing}

    for row in existing:
        if row.contact_id not in payload_ids:
            row.is_active = False
            row.updated_at = now

    for contact_id in payload.contact_ids:
        row = existing_by_contact.get(contact_id)
        if row is None:
            db.add(
                CnpjContact(
                    cnpj_id=cnpj_id,
                    contact_id=contact_id,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            row.is_active = True
            row.updated_at = now

    db.commit()
    return list_contacts_for_cnpj(db, cnpj_id)


def list_cnpjs_for_contact(
    db: Session, contact_id: int, *, include_inactive: bool = False
) -> list[CnpjRead]:
    _get_contact_or_404(db, contact_id)
    stmt = (
        select(Cnpj)
        .join(CnpjContact, CnpjContact.cnpj_id == Cnpj.id)
        .where(CnpjContact.contact_id == contact_id)
        .order_by(Cnpj.name.asc())
    )
    if not include_inactive:
        stmt = stmt.where(
            CnpjContact.is_active.is_(True),
            Cnpj.is_active.is_(True),
        )
    return [CnpjRead.model_validate(c) for c in db.scalars(stmt)]


def replace_cnpjs_for_contact(
    db: Session, contact_id: int, payload: CnpjIdsReplace
) -> list[CnpjRead]:
    _get_contact_or_404(db, contact_id)
    _validate_cnpj_ids(db, payload.cnpj_ids)

    now = _utc_now()
    payload_ids = set(payload.cnpj_ids)

    existing = list(
        db.scalars(
            select(CnpjContact).where(CnpjContact.contact_id == contact_id)
        )
    )
    existing_by_cnpj = {r.cnpj_id: r for r in existing}

    for row in existing:
        if row.cnpj_id not in payload_ids:
            row.is_active = False
            row.updated_at = now

    for cnpj_id in payload.cnpj_ids:
        row = existing_by_cnpj.get(cnpj_id)
        if row is None:
            db.add(
                CnpjContact(
                    cnpj_id=cnpj_id,
                    contact_id=contact_id,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            row.is_active = True
            row.updated_at = now

    db.commit()
    return list_cnpjs_for_contact(db, contact_id)
