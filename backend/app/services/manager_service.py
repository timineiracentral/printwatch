"""Dashboard gerencial — KPIs, comparativo e top 10 (ANAL-01..04, Fase 7)."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Department, PrintJob, Printer, User
from app.schemas.manager import ManagerSummaryResponse, PeriodKpi, TopEntry
from app.services.cost_service import (
    BUCKET_UNREGISTERED_PRINTER,
    BUCKET_UNREGISTERED_USER,
    _local_date_to_utc_range,
    line_cost,
    rate_at,
)
from app.services.policy_service import compute_outside_policy, load_policy_context

_TZ = ZoneInfo(settings.api_timezone)
_UTC = timezone.utc

PENDING_COLOR_MODE_THRESHOLD_PCT = 0.05

_TOP_LIMIT = 10


def previous_period_bounds(
    date_from: date, date_to: date, preset: str | None = None
) -> tuple[date, date]:
    """D-03: mês calendário anterior (preset month) ou mesma duração imediatamente antes."""
    if preset == "month":
        first_of_current = date_from.replace(day=1)
        prev_month_last = first_of_current - timedelta(days=1)
        prev_first = prev_month_last.replace(day=1)
        return prev_first, prev_month_last

    span_days = (date_to - date_from).days + 1
    prev_to = date_from - timedelta(days=1)
    prev_from = prev_to - timedelta(days=span_days - 1)
    return prev_from, prev_to


def _delta_pct(current: float, previous: float) -> float | None:
    if previous == 0:
        if current == 0:
            return 0.0
        return None
    return round((current - previous) / previous * 100.0, 1)


def _load_printers(db: Session) -> tuple[dict[int, str], dict[str, str]]:
    by_id: dict[int, str] = {}
    by_queue: dict[str, str] = {}
    for p in db.scalars(select(Printer).where(Printer.is_active.is_(True))).all():
        by_id[p.id] = p.display_name
        by_queue[p.cups_queue_name.lower()] = p.display_name
    return by_id, by_queue


def _load_users_departments(
    db: Session,
) -> tuple[dict[str, User], dict[int, Department]]:
    users = {
        u.cups_username.lower(): u
        for u in db.scalars(select(User).where(User.is_active.is_(True))).all()
    }
    departments = {
        d.id: d
        for d in db.scalars(select(Department).where(Department.is_active.is_(True))).all()
    }
    return users, departments


def _printer_display_name(
    job: PrintJob,
    printers_by_id: dict[int, str],
    printers_by_queue: dict[str, str],
) -> str:
    if job.printer_id is not None:
        return printers_by_id.get(job.printer_id, job.printer)
    queue = job.printer.lower()
    if queue in printers_by_queue:
        return printers_by_queue[queue]
    return BUCKET_UNREGISTERED_PRINTER


def _user_display_name(username: str, users: dict[str, User]) -> str:
    user = users.get(username.lower())
    if user is not None:
        return user.display_name
    return BUCKET_UNREGISTERED_USER


def _department_display_name(
    username: str, users: dict[str, User], departments: dict[int, Department]
) -> str:
    user = users.get(username.lower())
    if user is None:
        return BUCKET_UNREGISTERED_USER
    dept = departments.get(user.department_id)
    if dept is None:
        return BUCKET_UNREGISTERED_USER
    return dept.name


def _compute_period_kpi(
    db: Session,
    date_from: date,
    date_to: date,
    *,
    policy_ctx: Any | None = None,
    printers_by_id: dict[int, str] | None = None,
    printers_by_queue: dict[str, str] | None = None,
    users: dict[str, User] | None = None,
    departments: dict[int, Department] | None = None,
    accumulate_tops: bool = False,
) -> tuple[PeriodKpi, dict[str, dict[str, Any]] | None]:
    start_utc, _ = _local_date_to_utc_range(date_from)
    _, end_utc = _local_date_to_utc_range(date_to)

    if policy_ctx is None:
        policy_ctx = load_policy_context(db)
    if printers_by_id is None or printers_by_queue is None:
        printers_by_id, printers_by_queue = _load_printers(db)
    if users is None or departments is None:
        users, departments = _load_users_departments(db)

    pages_mono = 0
    pages_color = 0
    pages_pending = 0
    estimated_cost = Decimal("0")

    top_users: dict[str, dict[str, Any]] | None = (
        defaultdict(lambda: {"pages": 0, "cost": Decimal("0")})
        if accumulate_tops
        else None
    )
    top_printers: dict[str, dict[str, Any]] | None = (
        defaultdict(lambda: {"pages": 0, "cost": Decimal("0")})
        if accumulate_tops
        else None
    )
    top_depts: dict[str, dict[str, Any]] | None = (
        defaultdict(lambda: {"pages": 0, "cost": Decimal("0")})
        if accumulate_tops
        else None
    )

    stmt = (
        select(PrintJob)
        .where(PrintJob.timestamp >= start_utc)
        .where(PrintJob.timestamp <= end_utc)
    )

    for job in db.scalars(stmt):
        if compute_outside_policy(policy_ctx, job.username, job.printer_id):
            continue

        if job.color_mode is None:
            pages_pending += 1
            continue

        if job.color_mode == "mono":
            pages_mono += 1
        elif job.color_mode == "color":
            pages_color += 1
        else:
            continue

        rate = rate_at(db, job.timestamp)
        cost = line_cost(rate, job.color_mode) or Decimal("0")
        estimated_cost += cost

        if not accumulate_tops or top_users is None:
            continue

        uname = _user_display_name(job.username, users)
        top_users[uname]["pages"] += 1
        top_users[uname]["cost"] += cost

        pname = _printer_display_name(job, printers_by_id, printers_by_queue)
        top_printers[pname]["pages"] += 1
        top_printers[pname]["cost"] += cost

        dname = _department_display_name(job.username, users, departments)
        top_depts[dname]["pages"] += 1
        top_depts[dname]["cost"] += cost

    pages_billable = pages_mono + pages_color
    cost_out: Decimal | None = estimated_cost if estimated_cost > 0 else None

    kpi = PeriodKpi(
        pages_mono=pages_mono,
        pages_color=pages_color,
        pages_billable=pages_billable,
        pages_pending=pages_pending,
        estimated_cost=cost_out,
    )
    tops = None
    if accumulate_tops:
        tops = {
            "users": top_users or {},
            "printers": top_printers or {},
            "departments": top_depts or {},
        }
    return kpi, tops


def _tops_from_accumulator(
    acc: dict[str, dict[str, Any]], *, has_rates: bool
) -> list[TopEntry]:
    ranked = sorted(acc.items(), key=lambda x: x[1]["pages"], reverse=True)[
        :_TOP_LIMIT
    ]
    out: list[TopEntry] = []
    for name, data in ranked:
        cost = data["cost"]
        out.append(
            TopEntry(
                name=name,
                pages=data["pages"],
                estimated_cost=cost if has_rates and cost > 0 else None,
            )
        )
    return out


def _has_rates_in_period(db: Session, date_from: date, date_to: date) -> bool:
    _, end_utc = _local_date_to_utc_range(date_to)
    return rate_at(db, end_utc) is not None


def build_summary(
    db: Session,
    date_from: date,
    date_to: date,
    preset: str | None = None,
) -> ManagerSummaryResponse:
    policy_ctx = load_policy_context(db)
    printers_by_id, printers_by_queue = _load_printers(db)
    users, departments = _load_users_departments(db)

    period, tops_acc = _compute_period_kpi(
        db,
        date_from,
        date_to,
        policy_ctx=policy_ctx,
        printers_by_id=printers_by_id,
        printers_by_queue=printers_by_queue,
        users=users,
        departments=departments,
        accumulate_tops=True,
    )

    prev_from, prev_to = previous_period_bounds(date_from, date_to, preset)
    previous, _ = _compute_period_kpi(
        db,
        prev_from,
        prev_to,
        policy_ctx=policy_ctx,
        printers_by_id=printers_by_id,
        printers_by_queue=printers_by_queue,
        users=users,
        departments=departments,
        accumulate_tops=False,
    )

    period.previous = previous
    period.delta_pct_pages = _delta_pct(
        float(period.pages_billable), float(previous.pages_billable)
    )
    cur_cost = float(period.estimated_cost or 0)
    prev_cost = float(previous.estimated_cost or 0)
    period.delta_pct_cost = _delta_pct(cur_cost, prev_cost)

    has_rates = _has_rates_in_period(db, date_from, date_to)
    acc = tops_acc or {"users": {}, "printers": {}, "departments": {}}

    total_pages = period.pages_billable + period.pages_pending
    pending_pct: float | None = None
    if total_pages > 0:
        pending_pct = round(period.pages_pending / total_pages * 100.0, 2)

    return ManagerSummaryResponse(
        period=period,
        top_users=_tops_from_accumulator(acc["users"], has_rates=has_rates),
        top_printers=_tops_from_accumulator(acc["printers"], has_rates=has_rates),
        top_departments=_tops_from_accumulator(
            acc["departments"], has_rates=has_rates
        ),
        meter_reconciliation=[],
        has_rates=has_rates,
        pending_pct=pending_pct,
        pending_count=period.pages_pending,
    )
