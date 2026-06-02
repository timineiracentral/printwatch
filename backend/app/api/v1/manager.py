"""GET /api/v1/manager/summary (ANAL, Fase 7)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.manager import ManagerSummaryResponse
from app.services import manager_service

router = APIRouter()

_PRESET_PATTERN = "^(today|last7|last30|last90|month|custom)$"


@router.get("/summary", response_model=ManagerSummaryResponse)
def manager_summary_endpoint(
    date_from: date = Query(..., description="Início do período (inclusivo)"),
    date_to: date = Query(..., description="Fim do período (inclusivo)"),
    preset: str | None = Query(
        None,
        pattern=_PRESET_PATTERN,
        description="Preset de período para comparativo anterior (D-03)",
    ),
    db: Session = Depends(get_db_dep),
) -> ManagerSummaryResponse:
    if date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from must be less than or equal to date_to",
        )
    return manager_service.build_summary(
        db, date_from, date_to, preset=preset
    )
