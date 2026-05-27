"""CRUD /api/v1/users (D-06, D-07, D-17)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import users_service

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
