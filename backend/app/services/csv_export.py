"""Service de exportação CSV (EXPORT-01/02, D-11..D-19).

- Reutiliza `_build_aggregated_subquery` do `jobs_service` (D-11):
  o CSV reflete EXATAMENTE a mesma agregação que `/api/v1/jobs`.
- UTF-8 com BOM (`\\ufeff`), separador `;`, cabeçalhos pt-BR (D-12..D-14).
- StreamingResponse-compatible: `iter_csv_rows` é um generator —
  nada é materializado em memória; SQLAlchemy usa `yield_per=1000` (D-15).
- Cap de 100k linhas (D-16): chamadores devem usar `count_aggregated`
  antes para retornar 400 quando ultrapassar.
- Escape RFC 4180: valores com `;`, `"`, `\\n` ou `\\r` são envolvidos
  em aspas duplas com aspas internas duplicadas.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PrintJob
from app.schemas.jobs import JobFilters
from app.services.jobs_service import _build_aggregated_subquery

logger = logging.getLogger(__name__)

_TZ = ZoneInfo(settings.api_timezone)

MAX_CSV_ROWS = 100_000  # D-16
CSV_DELIMITER = ";"      # D-13
CSV_HEADER = [           # D-14 — cabeçalhos pt-BR
    "Data/Hora",
    "Usuário",
    "Impressora",
    "Documento",
    "Páginas",
    "Papel",
    "Frente/Verso",
    "Modo de Cor",
    "Origem",
]


def count_aggregated(db: Session, filters: JobFilters) -> int:
    """Contagem da subquery agregada para checagem do cap 100k (D-16)."""
    agg = _build_aggregated_subquery(filters).subquery()
    return db.execute(select(func.count()).select_from(agg)).scalar_one() or 0


def _csv_escape(value: Any) -> str:
    """RFC 4180: envolve em aspas e duplica aspas internas se necessário."""
    if value is None:
        return ""
    s = str(value)
    if any(c in s for c in (";", '"', "\n", "\r")):
        return '"' + s.replace('"', '""') + '"'
    return s


def _format_timestamp(ts: datetime) -> str:
    """UTC → America/Sao_Paulo, formato amigável Excel pt-BR."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(_TZ).strftime("%Y-%m-%d %H:%M:%S")


def make_filename() -> str:
    """`print_jobs_YYYYMMDD_HHMM.csv` no timezone configurado (D-17)."""
    return "print_jobs_" + datetime.now(_TZ).strftime("%Y%m%d_%H%M") + ".csv"


def iter_csv_rows(db: Session, filters: JobFilters) -> Iterator[str]:
    """Yields linha por linha do CSV agregado por job.

    - 1ª linha: BOM UTF-8 (D-12).
    - 2ª linha: cabeçalho pt-BR (D-14).
    - Demais: dados agregados, ordenados por timestamp DESC (D-07).
    """
    yield "\ufeff"
    yield CSV_DELIMITER.join(CSV_HEADER) + "\n"

    stmt = (
        _build_aggregated_subquery(filters)
        .order_by(func.min(PrintJob.timestamp).desc())
        .execution_options(yield_per=1000)
    )

    for row in db.execute(stmt).mappings():
        fields = [
            _format_timestamp(row["timestamp"]),
            row["username"] or "",
            row["printer"] or "",
            row["job_name"] or "",
            str(row["pages"]),
            row["media"] or "",
            row["sides"] or "",
            row["color_mode"] or "",
            row["host_origin"] or "",
        ]
        yield CSV_DELIMITER.join(_csv_escape(c) for c in fields) + "\n"
