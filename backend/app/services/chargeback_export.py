"""Exportação CSV de chargeback interno (CHRG-01..04, D-15..D-17).

- Dois arquivos por intervalo: centro de custo e departamento.
- Reutiliza `aggregate_cost_by_dimension` (exclui outside_policy).
- UTF-8 BOM, delimitador `;` — mesmo padrão de `csv_export.py`.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterator, Literal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.jobs import JobFilters
from app.services.cost_service import (
    BUCKET_PENDING_PAGES,
    aggregate_cost_by_dimension,
    format_money_brl,
)
from app.services.csv_export import CSV_DELIMITER, MAX_CSV_ROWS, _csv_escape
from app.services.stats_service import _month_bounds_local

_TZ = ZoneInfo(settings.api_timezone)

CHARGEBACK_HEADER = [
    "Grupo",
    "Páginas mono",
    "Páginas color",
    "Custo estimado (R$)",
]

ChargebackDimension = Literal["cost_center", "department"]


def resolve_chargeback_dates(filters: JobFilters) -> tuple[date, date]:
    """Intervalo do export: query params ou mês calendário corrente (SP)."""
    if filters.date_from is not None and filters.date_to is not None:
        return filters.date_from, filters.date_to
    if filters.date_from is not None:
        return filters.date_from, filters.date_from
    if filters.date_to is not None:
        return filters.date_to, filters.date_to
    return _month_bounds_local()


def count_chargeback_groups(
    db: Session,
    filters: JobFilters,
    dimension: ChargebackDimension,
) -> int:
    """Contagem de linhas (grupos + buckets) para cap 100k."""
    date_from, date_to = resolve_chargeback_dates(filters)
    rows = aggregate_cost_by_dimension(db, date_from, date_to, dimension)
    return len(rows)


def make_filename_cost_center() -> str:
    return "chargeback_cc_" + datetime.now(_TZ).strftime("%Y%m%d") + ".csv"


def make_filename_department() -> str:
    return "chargeback_dept_" + datetime.now(_TZ).strftime("%Y%m%d") + ".csv"


def _row_fields(row: dict) -> list[str]:
    mono = row["pages_mono"]
    color = row["pages_color"]
    if row["group_label"] == BUCKET_PENDING_PAGES:
        mono = row["pages_pending"]
    cost_str = format_money_brl(row["estimated_cost"]) or ""
    return [
        row["group_label"],
        str(mono),
        str(color),
        cost_str,
    ]


def iter_chargeback_csv(
    db: Session,
    filters: JobFilters,
    dimension: ChargebackDimension,
) -> Iterator[str]:
    """Generator compatível com StreamingResponse."""
    date_from, date_to = resolve_chargeback_dates(filters)
    yield "\ufeff"
    yield CSV_DELIMITER.join(CHARGEBACK_HEADER) + "\n"

    rows = aggregate_cost_by_dimension(db, date_from, date_to, dimension)
    for row in rows:
        fields = _row_fields(row)
        yield CSV_DELIMITER.join(_csv_escape(c) for c in fields) + "\n"
