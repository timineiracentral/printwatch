"""GET /api/v1/printers — DISTINCT printer FROM print_jobs (D-21).

NÃO consulta CUPS (lpstat, IPP). Endpoint informacional/histórico.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.services import jobs_service

router = APIRouter()


@router.get("", response_model=list[str])
def list_printers_endpoint(db: Session = Depends(get_db_dep)) -> list[str]:
    return jobs_service.list_printer_names(db)
