"""Service para /api/v1/stats/summary (D-20).

Reutiliza `_build_aggregated_subquery` do `jobs_service` (D-31):
qualquer mudança na definição de "job agregado" reflete automaticamente
no sumário, evitando drift entre o número total da listagem e o número
do bucket.

Janelas temporais:
- "hoje" = dia calendário local em `settings.api_timezone`
- "mês"  = mês calendário local (NÃO rolling 30d)
- "total" = todo o histórico no banco
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.jobs import JobFilters
from app.schemas.stats import StatsBucket, StatsSummaryResponse, TopEntry
from app.services.jobs_service import _build_aggregated_subquery

logger = logging.getLogger(__name__)

_TZ = ZoneInfo(settings.api_timezone)
_UTC = timezone.utc


def _today_bounds_local() -> tuple[date, date]:
    """Dia calendário local em SP (`date_from == date_to`)."""
    now_local = datetime.now(_TZ)
    today = now_local.date()
    return today, today


def _month_bounds_local() -> tuple[date, date]:
    """1º dia → último dia do mês corrente em SP (D-20)."""
    now_local = datetime.now(_TZ)
    first = now_local.date().replace(day=1)
    # Próximo mês → -1 dia = último dia do mês corrente.
    if first.month == 12:
        next_month_first = first.replace(year=first.year + 1, month=1)
    else:
        next_month_first = first.replace(month=first.month + 1)
    last = next_month_first - timedelta(days=1)
    return first, last


def _compute_bucket(
    db: Session, date_from: date | None, date_to: date | None, top_n: int
) -> StatsBucket:
    """Computa jobs, pages, top_users e top_printers do bucket."""
    filters = JobFilters(date_from=date_from, date_to=date_to)
    agg = _build_aggregated_subquery(filters).subquery()

    jobs = db.execute(select(func.count()).select_from(agg)).scalar_one() or 0
    pages = (
        db.execute(
            select(func.coalesce(func.sum(agg.c.pages), 0))
        ).scalar_one()
        or 0
    )

    top_users_stmt = (
        select(
            agg.c.username.label("name"),
            func.sum(agg.c.pages).label("pages"),
        )
        .group_by(agg.c.username)
        .order_by(func.sum(agg.c.pages).desc())
        .limit(top_n)
    )
    top_users = [
        TopEntry(name=r.name, pages=r.pages or 0)
        for r in db.execute(top_users_stmt)
    ]

    top_printers_stmt = (
        select(
            agg.c.printer.label("name"),
            func.sum(agg.c.pages).label("pages"),
        )
        .group_by(agg.c.printer)
        .order_by(func.sum(agg.c.pages).desc())
        .limit(top_n)
    )
    top_printers = [
        TopEntry(name=r.name, pages=r.pages or 0)
        for r in db.execute(top_printers_stmt)
    ]

    return StatsBucket(
        jobs=int(jobs),
        pages=int(pages),
        top_users=top_users,
        top_printers=top_printers,
    )


def compute_summary(db: Session, top_n: int = 5) -> StatsSummaryResponse:
    """Computa os 3 buckets do dashboard (hoje / mes / total)."""
    today_from, today_to = _today_bounds_local()
    month_from, month_to = _month_bounds_local()

    hoje = _compute_bucket(db, today_from, today_to, top_n)
    mes = _compute_bucket(db, month_from, month_to, top_n)
    total = _compute_bucket(db, None, None, top_n)

    return StatsSummaryResponse(hoje=hoje, mes=mes, total=total)
