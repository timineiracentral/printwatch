"""CRUD /api/v1/cost-rates — tarifas globais com histórico (D-01, D-03)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.cost_rates import CostRateCreate, CostRateRead
from app.services import cost_service

router = APIRouter()


@router.get("", response_model=list[CostRateRead])
def list_cost_rates_endpoint(
    db: Session = Depends(get_db_dep),
) -> list[CostRateRead]:
    return cost_service.list_cost_rates(db)


@router.get("/current", response_model=CostRateRead)
def get_current_cost_rate_endpoint(
    db: Session = Depends(get_db_dep),
) -> CostRateRead:
    row = cost_service.get_current_cost_rate(db)
    if row is None:
        raise HTTPException(status_code=404, detail="nenhuma tarifa configurada")
    return row


@router.post("", response_model=CostRateRead, status_code=201)
def create_cost_rate_endpoint(
    payload: CostRateCreate,
    db: Session = Depends(get_db_dep),
) -> CostRateRead:
    return cost_service.create_cost_rate(db, payload)
