"""GET /api/v1/jobs, linhas brutas e correção de color_mode (D-01..D-10, D-08)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.common import Page
from app.schemas.job_lines import ColorModePatch, JobLineFilters, JobLineOut
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


@router.get("/lines", response_model=list[JobLineOut])
def list_job_lines_endpoint(
    filters: Annotated[JobLineFilters, Query()],
    db: Session = Depends(get_db_dep),
) -> list[dict]:
    return jobs_service.list_job_lines(db, filters)


@router.patch("/lines/{line_id}/color-mode", response_model=JobLineOut)
def patch_line_color_mode_endpoint(
    line_id: int,
    payload: ColorModePatch,
    db: Session = Depends(get_db_dep),
) -> dict:
    row = jobs_service.patch_line_color_mode(db, line_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="print job line not found")
    return {
        "id": row.id,
        "timestamp": row.timestamp,
        "color_mode": row.color_mode,
        "color_mode_source": row.color_mode_source,
        "pages": 1,
    }


@router.get("/{job_id}", response_model=JobOut)
def get_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db_dep),
) -> dict:
    row = jobs_service.get_job_by_id(db, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    return row
