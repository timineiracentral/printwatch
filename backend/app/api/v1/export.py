"""GET /api/v1/export/csv (EXPORT-01..04, D-11..D-19)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.jobs import JobFilters
from app.services import csv_export

router = APIRouter()


@router.get("/csv")
def export_csv_endpoint(
    filters: JobFilters = Depends(),
    db: Session = Depends(get_db_dep),
) -> StreamingResponse:
    total = csv_export.count_aggregated(db, filters)
    if total > csv_export.MAX_CSV_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Export excede {csv_export.MAX_CSV_ROWS:,} linhas "
                f"(filtro retorna {total:,}). Restrinja por data ou impressora."
            ),
        )

    filename = csv_export.make_filename()
    return StreamingResponse(
        csv_export.iter_csv_rows(db, filters),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Rows": str(total),
        },
    )
