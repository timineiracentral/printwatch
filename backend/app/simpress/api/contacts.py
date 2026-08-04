"""CRUD /api/v1/simpress/contacts + link CNPJs (CNPJ-02)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.simpress.db.session import get_simpress_db
from app.simpress.schemas.cnpj import CnpjRead
from app.simpress.schemas.contact import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
    CnpjIdsReplace,
)
from app.simpress.services import contacts_service, links_service

router = APIRouter()


@router.get("", response_model=list[ContactRead])
def list_contacts_endpoint(
    db: Session = Depends(get_simpress_db),
    q: Optional[str] = Query(None, description="Busca em name ou phone"),
    include_inactive: bool = Query(
        False, description="Incluir contatos com is_active=false"
    ),
) -> list[ContactRead]:
    return contacts_service.list_contacts(
        db, include_inactive=include_inactive, q=q
    )


@router.post("", response_model=ContactRead, status_code=201)
def create_contact_endpoint(
    payload: ContactCreate,
    db: Session = Depends(get_simpress_db),
) -> ContactRead:
    return contacts_service.create_contact(db, payload)


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact_endpoint(
    contact_id: int,
    db: Session = Depends(get_simpress_db),
) -> ContactRead:
    row = contacts_service.get_contact_by_id(db, contact_id)
    if row is None:
        raise HTTPException(status_code=404, detail="contact not found")
    return row


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact_endpoint(
    contact_id: int,
    payload: ContactUpdate,
    db: Session = Depends(get_simpress_db),
) -> ContactRead:
    return contacts_service.update_contact(db, contact_id, payload)


@router.delete("/{contact_id}", response_model=ContactRead)
def delete_contact_endpoint(
    contact_id: int,
    db: Session = Depends(get_simpress_db),
) -> ContactRead:
    return contacts_service.soft_delete_contact(db, contact_id)


@router.get("/{contact_id}/cnpjs", response_model=list[CnpjRead])
def list_contact_cnpjs_endpoint(
    contact_id: int,
    db: Session = Depends(get_simpress_db),
    include_inactive: bool = Query(False),
) -> list[CnpjRead]:
    return links_service.list_cnpjs_for_contact(
        db, contact_id, include_inactive=include_inactive
    )


@router.put("/{contact_id}/cnpjs", response_model=list[CnpjRead])
def replace_contact_cnpjs_endpoint(
    contact_id: int,
    payload: CnpjIdsReplace,
    db: Session = Depends(get_simpress_db),
) -> list[CnpjRead]:
    return links_service.replace_cnpjs_for_contact(db, contact_id, payload)
