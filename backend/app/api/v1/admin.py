"""Endpoints administrativos (backfill matcher, D-04)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.services.printer_matcher import count_remaining_null, match_batch

router = APIRouter()

_MAX_BACKFILL_ITERATIONS = 1000


class BackfillPrinterIdsResponse(BaseModel):
    matched_total: int
    remaining_null: int


@router.post("/backfill-printer-ids", response_model=BackfillPrinterIdsResponse)
def backfill_printer_ids(db: Session = Depends(get_db_dep)) -> BackfillPrinterIdsResponse:
    """Backfill idempotente: batches de 500 até estabilizar ou max_iterations."""
    matched_total = 0
    for _ in range(_MAX_BACKFILL_ITERATIONS):
        n = match_batch(db, limit=500)
        matched_total += n
        if n == 0:
            break
    return BackfillPrinterIdsResponse(
        matched_total=matched_total,
        remaining_null=count_remaining_null(db),
    )
