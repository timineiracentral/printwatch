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

from decimal import Decimal

from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PrintJob
from app.schemas.job_lines import ColorModePatch, JobLineFilters
from app.schemas.jobs import JobFilters
from app.services.cost_service import line_cost, rate_at
from app.services.policy_service import compute_outside_policy, load_policy_context

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
    pages_mono_expr = func.sum(
        case((PrintJob.color_mode == "mono", 1), else_=0)
    )
    pages_color_expr = func.sum(
        case((PrintJob.color_mode == "color", 1), else_=0)
    )
    pages_pending_expr = func.sum(
        case((PrintJob.color_mode.is_(None), 1), else_=0)
    )

    stmt = (
        select(
            PrintJob.printer.label("printer"),
            PrintJob.username.label("username"),
            PrintJob.job_id.label("job_id"),
            PrintJob.job_name.label("job_name"),
            minute_bucket.label("minute_bucket"),
            func.min(PrintJob.timestamp).label("timestamp"),
            func.count().label("pages"),
            pages_mono_expr.label("pages_mono"),
            pages_color_expr.label("pages_color"),
            pages_pending_expr.label("pages_pending_color"),
            func.max(PrintJob.color_mode).label("color_mode"),
            func.max(PrintJob.host_origin).label("host_origin"),
            func.max(PrintJob.media).label("media"),
            func.max(PrintJob.sides).label("sides"),
            func.max(PrintJob.printer_id).label("printer_id"),
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


def _normalize_count_fields(item: dict[str, Any]) -> None:
    """Garante int nos contadores agregados (SQLite pode retornar None)."""
    mono = int(item.get("pages_mono") or 0)
    color = int(item.get("pages_color") or 0)
    pending = int(item.get("pages_pending_color") or 0)
    item["pages_mono"] = mono
    item["pages_color"] = color
    item["pages_pending_color"] = pending
    item["pages_billable"] = mono + color


def _sum_estimated_cost(db: Session, lines: list[PrintJob]) -> Decimal | None:
    """Soma line_cost das linhas faturáveis; None se nenhuma linha teve custo."""
    total = Decimal("0")
    any_cost = False
    rate_cache: dict[datetime, object] = {}
    for line in lines:
        if line.color_mode not in ("mono", "color"):
            continue
        ts = line.timestamp
        if ts not in rate_cache:
            rate_cache[ts] = rate_at(db, ts)
        cost = line_cost(rate_cache[ts], line.color_mode)
        if cost is not None:
            total += cost
            any_cost = True
    return total if any_cost else None


def _group_where_clauses(item: dict[str, Any]) -> list:
    minute_bucket = func.strftime("%Y-%m-%d %H:%M", PrintJob.timestamp)
    clauses = [
        PrintJob.printer == item["printer"],
        PrintJob.username == item["username"],
        PrintJob.job_id == item["job_id"],
        minute_bucket == item["minute_bucket"],
    ]
    if item.get("job_name") is None:
        clauses.append(PrintJob.job_name.is_(None))
    else:
        clauses.append(PrintJob.job_name == item["job_name"])
    return clauses


def _enrich_estimated_cost(db: Session, items: list[dict[str, Any]]) -> None:
    if not items:
        return
    for item in items:
        lines = list(
            db.scalars(
                select(PrintJob).where(*_group_where_clauses(item))
            ).all()
        )
        item["estimated_cost"] = _sum_estimated_cost(db, lines)


def _enrich_billable_fields(db: Session, items: list[dict[str, Any]]) -> None:
    for item in items:
        _normalize_count_fields(item)
    _enrich_estimated_cost(db, items)


def _enrich_outside_policy(
    db: Session, items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    ctx = load_policy_context(db)
    for item in items:
        item["outside_policy"] = compute_outside_policy(
            ctx, item["username"], item.get("printer_id")
        )
    return items


def _apply_outside_policy_filter(
    items: list[dict[str, Any]], filters: JobFilters
) -> list[dict[str, Any]]:
    if filters.outside_policy is None:
        return items
    want = filters.outside_policy
    return [i for i in items if i.get("outside_policy") is want]


# Alias público para imports cross-service (D-31 — citado em RESEARCH §6).
_build_aggregated_subquery = _build_aggregated_query


def list_jobs(db: Session, filters: JobFilters) -> tuple[list[dict[str, Any]], int]:
    """Lista paginada de jobs agregados (D-07, D-08)."""
    if filters.outside_policy is not None:
        stmt_all = _build_aggregated_query(filters).order_by(
            func.min(PrintJob.timestamp).desc()
        )
        rows_all = db.execute(stmt_all).mappings().all()
        items = _enrich_outside_policy(db, [dict(r) for r in rows_all])
        _enrich_billable_fields(db, items)
        items = _apply_outside_policy_filter(items, filters)
        total = len(items)
        start = (filters.page - 1) * filters.size
        end = start + filters.size
        return items[start:end], total

    agg = _build_aggregated_query(filters).subquery()
    total = db.execute(select(func.count()).select_from(agg)).scalar_one()

    stmt = (
        _build_aggregated_query(filters)
        .order_by(func.min(PrintJob.timestamp).desc())
        .limit(filters.size)
        .offset((filters.page - 1) * filters.size)
    )
    rows = db.execute(stmt).mappings().all()

    items = _enrich_outside_policy(db, [dict(r) for r in rows])
    _enrich_billable_fields(db, items)
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

    minute_bucket_label = row.timestamp.strftime("%Y-%m-%d %H:%M")

    stmt = (
        select(
            PrintJob.printer.label("printer"),
            PrintJob.username.label("username"),
            PrintJob.job_id.label("job_id"),
            PrintJob.job_name.label("job_name"),
            func.min(PrintJob.timestamp).label("timestamp"),
            func.count().label("pages"),
            func.sum(
                case((PrintJob.color_mode == "mono", 1), else_=0)
            ).label("pages_mono"),
            func.sum(
                case((PrintJob.color_mode == "color", 1), else_=0)
            ).label("pages_color"),
            func.sum(
                case((PrintJob.color_mode.is_(None), 1), else_=0)
            ).label("pages_pending_color"),
            func.max(PrintJob.color_mode).label("color_mode"),
            func.max(PrintJob.host_origin).label("host_origin"),
            func.max(PrintJob.media).label("media"),
            func.max(PrintJob.sides).label("sides"),
            func.max(PrintJob.printer_id).label("printer_id"),
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
    out["minute_bucket"] = minute_bucket_label
    enriched = _enrich_outside_policy(db, [out])
    _enrich_billable_fields(db, enriched)
    return enriched[0]


def list_job_lines(db: Session, filters: JobLineFilters) -> list[dict[str, Any]]:
    """Linhas brutas do grupo agregado (correção manual D-08)."""
    item = {
        "printer": filters.printer,
        "username": filters.username,
        "job_id": filters.job_id,
        "job_name": filters.job_name,
        "minute_bucket": filters.minute_bucket,
    }
    stmt = (
        select(PrintJob)
        .where(*_group_where_clauses(item))
        .order_by(PrintJob.timestamp.asc())
    )
    rows = db.scalars(stmt).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp,
            "color_mode": r.color_mode,
            "color_mode_source": r.color_mode_source,
            "pages": 1,
        }
        for r in rows
    ]


def patch_line_color_mode(
    db: Session, line_id: int, payload: ColorModePatch
) -> PrintJob | None:
    """Atualiza color_mode e marca source=manual (D-08)."""
    row = db.get(PrintJob, line_id)
    if row is None:
        return None
    row.color_mode = payload.color_mode
    row.color_mode_source = "manual"
    db.commit()
    db.refresh(row)
    return row


def backfill_mono_only_printer(db: Session, printer_queue: str) -> int:
    """Reclassifica linhas históricas da impressora como mono_only.

    Respeita correções manuais: WHERE color_mode_source != 'manual'.
    """
    result = db.execute(
        update(PrintJob)
        .where(PrintJob.printer == printer_queue)
        .where(PrintJob.color_mode_source != "manual")
        .values(color_mode="mono", color_mode_source="mono_only")
    )
    db.commit()
    return result.rowcount


def list_printer_names(db: Session) -> list[str]:
    """DISTINCT printer FROM print_jobs (D-21 — SEM consultar CUPS)."""
    stmt = select(PrintJob.printer).distinct().order_by(PrintJob.printer.asc())
    return [r[0] for r in db.execute(stmt) if r[0] is not None]
