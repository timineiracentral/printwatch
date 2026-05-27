"""CRUD /api/v1/departments (D-15, D-16)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services import departments_service

router = APIRouter()


@router.get("", response_model=list[DepartmentRead])
def list_departments_endpoint(
    db: Session = Depends(get_db_dep),
    q: Optional[str] = Query(None, description="Busca em code ou name"),
    include_inactive: bool = Query(
        False, description="Incluir departamentos com is_active=false"
    ),
) -> list[DepartmentRead]:
    return departments_service.list_departments(
        db, include_inactive=include_inactive, q=q
    )


@router.post("", response_model=DepartmentRead, status_code=201)
def create_department_endpoint(
    payload: DepartmentCreate,
    db: Session = Depends(get_db_dep),
) -> DepartmentRead:
    return departments_service.create_department(db, payload)


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department_endpoint(
    department_id: int,
    db: Session = Depends(get_db_dep),
) -> DepartmentRead:
    row = departments_service.get_department_by_id(db, department_id)
    if row is None:
        raise HTTPException(status_code=404, detail="department not found")
    return row


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department_endpoint(
    department_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db_dep),
) -> DepartmentRead:
    return departments_service.update_department(db, department_id, payload)


@router.delete("/{department_id}", response_model=DepartmentRead)
def delete_department_endpoint(
    department_id: int,
    db: Session = Depends(get_db_dep),
) -> DepartmentRead:
    return departments_service.soft_delete_department(db, department_id)
