"""GET /api/v1/stats/summary (D-20)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.stats import StatsSummaryResponse
from app.services import stats_service

router = APIRouter()


@router.get("/summary", response_model=StatsSummaryResponse)
def stats_summary_endpoint(
    top: int = Query(
        5,
        ge=1,
        le=50,
        description="Quantos itens em top_users/top_printers (1..50, default 5)",
    ),
    db: Session = Depends(get_db_dep),
) -> StatsSummaryResponse:
    return stats_service.compute_summary(db, top_n=top)
