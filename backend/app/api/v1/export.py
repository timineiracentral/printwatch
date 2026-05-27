"""GET /api/v1/export/csv e chargeback (EXPORT-01..04, CHRG-01..04)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.jobs import JobFilters
from app.services import chargeback_export, csv_export
from app.services.chargeback_export import ChargebackDimension

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


def _chargeback_streaming_response(
    db: Session,
    filters: JobFilters,
    dimension: ChargebackDimension,
    filename: str,
) -> StreamingResponse:
    total = chargeback_export.count_chargeback_groups(db, filters, dimension)
    if total > csv_export.MAX_CSV_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Export excede {csv_export.MAX_CSV_ROWS:,} grupos "
                f"(filtro retorna {total:,}). Restrinja por data."
            ),
        )
    return StreamingResponse(
        chargeback_export.iter_chargeback_csv(db, filters, dimension),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Rows": str(total),
        },
    )


@router.get("/chargeback/by-cost-center")
def export_chargeback_by_cost_center(
    filters: JobFilters = Depends(),
    db: Session = Depends(get_db_dep),
) -> StreamingResponse:
    """CSV chargeback por centro de custo.

    Query: `date_from`, `date_to` (opcionais — default: mês calendário corrente em SP).
    """
    return _chargeback_streaming_response(
        db,
        filters,
        "cost_center",
        chargeback_export.make_filename_cost_center(),
    )


@router.get("/chargeback/by-department")
def export_chargeback_by_department(
    filters: JobFilters = Depends(),
    db: Session = Depends(get_db_dep),
) -> StreamingResponse:
    """CSV chargeback por departamento.

    Query: `date_from`, `date_to` (opcionais — default: mês calendário corrente em SP).
    """
    return _chargeback_streaming_response(
        db,
        filters,
        "department",
        chargeback_export.make_filename_department(),
    )
