"""CRUD /api/v1/cost-centers (D-15, D-16)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.cost_center import CostCenterCreate, CostCenterRead, CostCenterUpdate
from app.services import cost_centers_service

router = APIRouter()


@router.get("", response_model=list[CostCenterRead])
def list_cost_centers_endpoint(
    db: Session = Depends(get_db_dep),
    q: Optional[str] = Query(None, description="Busca em code ou name"),
    include_inactive: bool = Query(
        False, description="Incluir centros de custo com is_active=false"
    ),
) -> list[CostCenterRead]:
    return cost_centers_service.list_cost_centers(
        db, include_inactive=include_inactive, q=q
    )


@router.post("", response_model=CostCenterRead, status_code=201)
def create_cost_center_endpoint(
    payload: CostCenterCreate,
    db: Session = Depends(get_db_dep),
) -> CostCenterRead:
    return cost_centers_service.create_cost_center(db, payload)


@router.get("/{cost_center_id}", response_model=CostCenterRead)
def get_cost_center_endpoint(
    cost_center_id: int,
    db: Session = Depends(get_db_dep),
) -> CostCenterRead:
    row = cost_centers_service.get_cost_center_by_id(db, cost_center_id)
    if row is None:
        raise HTTPException(status_code=404, detail="cost center not found")
    return row


@router.patch("/{cost_center_id}", response_model=CostCenterRead)
def update_cost_center_endpoint(
    cost_center_id: int,
    payload: CostCenterUpdate,
    db: Session = Depends(get_db_dep),
) -> CostCenterRead:
    return cost_centers_service.update_cost_center(db, cost_center_id, payload)


@router.delete("/{cost_center_id}", response_model=CostCenterRead)
def delete_cost_center_endpoint(
    cost_center_id: int,
    db: Session = Depends(get_db_dep),
) -> CostCenterRead:
    return cost_centers_service.soft_delete_cost_center(db, cost_center_id)
