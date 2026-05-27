"""GET /api/v1/jobs e /api/v1/jobs/{job_id} (D-01..D-10)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.common import Page
from app.schemas.jobs import JobFilters, JobOut
from app.services import jobs_service

router = APIRouter()


@router.get("", response_model=Page[JobOut])
def list_jobs_endpoint(
    filters: Annotated[JobFilters, Query()],
    db: Session = Depends(get_db_dep),
) -> Page[JobOut]:
    items, total = jobs_service.list_jobs(db, filters)
    return Page[JobOut](
        items=items,
        total=total,
        page=filters.page,
        size=filters.size,
    )


@router.get("/{job_id}", response_model=JobOut)
def get_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db_dep),
) -> dict:
    row = jobs_service.get_job_by_id(db, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    return row
