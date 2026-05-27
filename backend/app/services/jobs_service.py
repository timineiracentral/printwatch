"""Service para listagem agregada de jobs (D-01..D-10, D-21).

Reutiliza `PrintJobRepository` da Fase 2 (D-31): não cria uma segunda
camada repository paralela — service simples com `Session` e queries
SQLAlchemy explícitas.

A agregação por job (D-04) é implementada via SQL `GROUP BY` sobre
`(printer, job_id, username, job_name, strftime('%Y-%m-%d %H:%M',
timestamp))`. Isso colapsa as N linhas do `page_log` que compõem um
único job de impressão em uma única linha de resposta.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PrintJob
from app.schemas.jobs import JobFilters

logger = logging.getLogger(__name__)

_TZ = ZoneInfo(settings.api_timezone)
_UTC = timezone.utc


def _local_date_to_utc_range(d: date) -> tuple[datetime, datetime]:
    """Converte um `date` local SP em (start_utc, end_utc) inclusivos.

    Usado para interpretar `date_from`/`date_to` (D-09, D-10):
    bounds são `00:00:00` e `23:59:59.999999` no timezone do operador.
    """
    start_local = datetime.combine(d, time(0, 0, 0), tzinfo=_TZ)
    end_local = datetime.combine(d, time(23, 59, 59, 999_999), tzinfo=_TZ)
    return start_local.astimezone(_UTC), end_local.astimezone(_UTC)


def _build_aggregated_query(filters: JobFilters):
    """Constrói o SELECT agregado por job — reutilizável (D-04, D-31).

    Retorna um statement SQLAlchemy (Select) com:
      - colunas agregadas conforme D-04
      - WHERE com filtros opcionais (D-09)
      - GROUP BY conforme D-04/D-05
    Sem ORDER BY/LIMIT/OFFSET — chamadores aplicam por cima.

    Esta função é importada por stats_service (Plano 04) e csv_export
    (Plano 05) — daí o nome público (sem underscore?). Mantido com
    underscore para sinalizar "API interna de services", mas o plano
    referencia explicitamente (D-31).
    """
    minute_bucket = func.strftime("%Y-%m-%d %H:%M", PrintJob.timestamp)

    stmt = (
        select(
            PrintJob.printer.label("printer"),
            PrintJob.username.label("username"),
            PrintJob.job_id.label("job_id"),
            PrintJob.job_name.label("job_name"),
            func.min(PrintJob.timestamp).label("timestamp"),
            func.count().label("pages"),
            func.max(PrintJob.color_mode).label("color_mode"),
            func.max(PrintJob.host_origin).label("host_origin"),
            func.max(PrintJob.media).label("media"),
            func.max(PrintJob.sides).label("sides"),
        )
        .group_by(
            PrintJob.printer,
            PrintJob.username,
            PrintJob.job_id,
            PrintJob.job_name,
            minute_bucket,
        )
    )

    if filters.username:
        stmt = stmt.where(
            func.lower(PrintJob.username).contains(filters.username.lower())
        )
    if filters.printer:
        stmt = stmt.where(PrintJob.printer == filters.printer)
    if filters.search:
        stmt = stmt.where(
            func.lower(PrintJob.job_name).contains(filters.search.lower())
        )
    if filters.date_from is not None:
        start_utc, _ = _local_date_to_utc_range(filters.date_from)
        stmt = stmt.where(PrintJob.timestamp >= start_utc)
    if filters.date_to is not None:
        _, end_utc = _local_date_to_utc_range(filters.date_to)
        stmt = stmt.where(PrintJob.timestamp <= end_utc)

    return stmt


# Alias público para imports cross-service (D-31 — citado em RESEARCH §6).
_build_aggregated_subquery = _build_aggregated_query


def list_jobs(db: Session, filters: JobFilters) -> tuple[list[dict[str, Any]], int]:
    """Lista paginada de jobs agregados (D-07, D-08)."""
    agg = _build_aggregated_query(filters).subquery()
    total = db.execute(select(func.count()).select_from(agg)).scalar_one()

    stmt = (
        _build_aggregated_query(filters)
        .order_by(func.min(PrintJob.timestamp).desc())
        .limit(filters.size)
        .offset((filters.page - 1) * filters.size)
    )
    rows = db.execute(stmt).mappings().all()

    items: list[dict[str, Any]] = [dict(r) for r in rows]
    return items, total


def get_job_by_id(db: Session, job_db_id: int) -> dict[str, Any] | None:
    """Retorna o job agregado correspondente ao `PrintJob.id` (D-04).

    O id natural identifica uma página específica do page_log;
    re-agregamos o grupo inteiro a partir da chave de agregação dele.
    """
    row = db.execute(
        select(PrintJob).where(PrintJob.id == job_db_id)
    ).scalar_one_or_none()
    if row is None:
        return None

    # Para casar o `strftime` de TEXT vs DATETIME do row.timestamp,
    # usamos func.strftime com bind param.
    minute_bucket = func.strftime("%Y-%m-%d %H:%M", PrintJob.timestamp)
    row_minute = row.timestamp.strftime("%Y-%m-%d %H:%M")

    where_clauses = [
        PrintJob.printer == row.printer,
        PrintJob.job_id == row.job_id,
        PrintJob.username == row.username,
        minute_bucket == row_minute,
    ]
    if row.job_name is None:
        where_clauses.append(PrintJob.job_name.is_(None))
    else:
        where_clauses.append(PrintJob.job_name == row.job_name)

    stmt = (
        select(
            PrintJob.printer.label("printer"),
            PrintJob.username.label("username"),
            PrintJob.job_id.label("job_id"),
            PrintJob.job_name.label("job_name"),
            func.min(PrintJob.timestamp).label("timestamp"),
            func.count().label("pages"),
            func.max(PrintJob.color_mode).label("color_mode"),
            func.max(PrintJob.host_origin).label("host_origin"),
            func.max(PrintJob.media).label("media"),
            func.max(PrintJob.sides).label("sides"),
        )
        .where(*where_clauses)
        .group_by(
            PrintJob.printer,
            PrintJob.username,
            PrintJob.job_id,
            PrintJob.job_name,
        )
    )
    result = db.execute(stmt).mappings().first()
    if result is None:
        return None
    out = dict(result)
    out["id"] = row.id
    return out


def list_printer_names(db: Session) -> list[str]:
    """DISTINCT printer FROM print_jobs (D-21 — SEM consultar CUPS)."""
    stmt = select(PrintJob.printer).distinct().order_by(PrintJob.printer.asc())
    return [r[0] for r in db.execute(stmt) if r[0] is not None]
