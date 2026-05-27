"""CRUD /api/v1/users (D-06, D-07, D-17) + printer-access + ti-export."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.user_printer_access import PrinterAccessRead, PrinterAccessReplace
from app.services import ti_export_service, user_printer_access_service, users_service

router = APIRouter()


@router.get("", response_model=list[UserRead])
def list_users_endpoint(
    db: Session = Depends(get_db_dep),
    department_id: Optional[int] = Query(
        None, description="Filtrar por departamento"
    ),
    cost_center_id: Optional[int] = Query(
        None, description="Filtrar por centro de custo"
    ),
    q: Optional[str] = Query(
        None, description="Busca em cups_username ou display_name"
    ),
    include_inactive: bool = Query(
        False, description="Incluir usuários com is_active=false"
    ),
) -> list[UserRead]:
    return users_service.list_users(
        db,
        include_inactive=include_inactive,
        department_id=department_id,
        cost_center_id=cost_center_id,
        q=q,
    )


@router.post("", response_model=UserRead, status_code=201)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db_dep),
) -> UserRead:
    return users_service.create_user(db, payload)


@router.get("/{user_id}/printer-access", response_model=list[PrinterAccessRead])
def get_user_printer_access_endpoint(
    user_id: int,
    db: Session = Depends(get_db_dep),
    include_inactive: bool = Query(False),
) -> list[PrinterAccessRead]:
    return user_printer_access_service.list_for_user(
        db, user_id, include_inactive=include_inactive
    )


@router.put("/{user_id}/printer-access", response_model=list[PrinterAccessRead])
def put_user_printer_access_endpoint(
    user_id: int,
    payload: PrinterAccessReplace,
    db: Session = Depends(get_db_dep),
) -> list[PrinterAccessRead]:
    return user_printer_access_service.replace_for_user(db, user_id, payload)


@router.get("/{user_id}/ti-export")
def get_user_ti_export_endpoint(
    user_id: int,
    db: Session = Depends(get_db_dep),
    format: Optional[str] = Query(None, alias="format"),
):
    rows = ti_export_service.build_ti_export_rows(db, user_id)
    if format == "csv":
        csv_body = ti_export_service.iter_ti_export_csv(rows)
        return PlainTextResponse(
            content=csv_body,
            media_type="text/csv; charset=utf-8",
        )
    return rows


@router.get("/{user_id}", response_model=UserRead)
def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db_dep),
) -> UserRead:
    row = users_service.get_user_by_id(db, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    return row


@router.patch("/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db_dep),
) -> UserRead:
    return users_service.update_user(db, user_id, payload)


@router.delete("/{user_id}", response_model=UserRead)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db_dep),
) -> UserRead:
    return users_service.soft_delete_user(db, user_id)
