"""CRUD /api/v1/simpress/cnpjs + link contacts (CNPJ-01)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.simpress.db.session import get_simpress_db
from app.simpress.schemas.cnpj import (
    CnpjCreate,
    CnpjRead,
    CnpjUpdate,
    ContactIdsReplace,
)
from app.simpress.schemas.contact import ContactRead
from app.simpress.services import cnpjs_service, links_service

router = APIRouter()


@router.get("", response_model=list[CnpjRead])
def list_cnpjs_endpoint(
    db: Session = Depends(get_simpress_db),
    q: Optional[str] = Query(None, description="Busca em cnpj ou name"),
    include_inactive: bool = Query(
        False, description="Incluir CNPJs com is_active=false"
    ),
) -> list[CnpjRead]:
    return cnpjs_service.list_cnpjs(db, include_inactive=include_inactive, q=q)


@router.post("", response_model=CnpjRead, status_code=201)
def create_cnpj_endpoint(
    payload: CnpjCreate,
    db: Session = Depends(get_simpress_db),
) -> CnpjRead:
    return cnpjs_service.create_cnpj(db, payload)


@router.get("/{cnpj_id}", response_model=CnpjRead)
def get_cnpj_endpoint(
    cnpj_id: int,
    db: Session = Depends(get_simpress_db),
) -> CnpjRead:
    row = cnpjs_service.get_cnpj_by_id(db, cnpj_id)
    if row is None:
        raise HTTPException(status_code=404, detail="cnpj not found")
    return row


@router.patch("/{cnpj_id}", response_model=CnpjRead)
def update_cnpj_endpoint(
    cnpj_id: int,
    payload: CnpjUpdate,
    db: Session = Depends(get_simpress_db),
) -> CnpjRead:
    return cnpjs_service.update_cnpj(db, cnpj_id, payload)


@router.delete("/{cnpj_id}", response_model=CnpjRead)
def delete_cnpj_endpoint(
    cnpj_id: int,
    db: Session = Depends(get_simpress_db),
) -> CnpjRead:
    return cnpjs_service.soft_delete_cnpj(db, cnpj_id)


@router.get("/{cnpj_id}/contacts", response_model=list[ContactRead])
def list_cnpj_contacts_endpoint(
    cnpj_id: int,
    db: Session = Depends(get_simpress_db),
    include_inactive: bool = Query(False),
) -> list[ContactRead]:
    return links_service.list_contacts_for_cnpj(
        db, cnpj_id, include_inactive=include_inactive
    )


@router.put("/{cnpj_id}/contacts", response_model=list[ContactRead])
def replace_cnpj_contacts_endpoint(
    cnpj_id: int,
    payload: ContactIdsReplace,
    db: Session = Depends(get_simpress_db),
) -> list[ContactRead]:
    return links_service.replace_contacts_for_cnpj(db, cnpj_id, payload)
