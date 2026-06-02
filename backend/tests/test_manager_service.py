"""Testes manager_service — KPIs, tops, comparativo, performance (07-02)."""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.db.models import CostRate, Department, PrintJob, Printer, User, UserPrinterAccess
from app.services.cost_service import BUCKET_UNREGISTERED_USER
from app.services.manager_service import (
    build_summary,
    previous_period_bounds,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_manager_fixtures(db: Session) -> dict:
    """Org mínima: dept, user, printers, rate, policy access."""
    now = _utc_now()
    dept = Department(
        code="TI",
        name="Tecnologia",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(dept)
    db.flush()

    user = User(
        cups_username="alice",
        display_name="Alice",
        department_id=dept.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    allowed = Printer(
        display_name="Lab A",
        cups_queue_name="lab_a",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    other = Printer(
        display_name="Lab B",
        cups_queue_name="lab_b",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add_all([user, allowed, other])
    db.flush()
    db.add(
        UserPrinterAccess(
            user_id=user.id,
            printer_id=allowed.id,
            is_active=True,
            is_default=True,
            created_at=now,
            updated_at=now,
        )
    )
    db.add(
        CostRate(
            rate_mono=Decimal("0.10"),
            rate_color=Decimal("0.40"),
            valid_from=datetime(2026, 1, 1),
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
    return {"user": user, "allowed": allowed, "other": other, "dept": dept}


def test_kpi_billable_pages(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    ts = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(3):
        db_session.add(
            PrintJob(
                printer=fx["allowed"].cups_queue_name,
                printer_id=fx["allowed"].id,
                username="alice",
                job_id=100 + i,
                timestamp=ts,
                pages=1,
                color_mode="mono",
            )
        )
    db_session.add(
        PrintJob(
            printer=fx["allowed"].cups_queue_name,
            printer_id=fx["allowed"].id,
            username="alice",
            job_id=200,
            timestamp=ts,
            pages=1,
            color_mode=None,
        )
    )
    db_session.commit()

    summary = build_summary(db_session, date(2026, 5, 1), date(2026, 5, 31))
    assert summary.period.pages_billable == 3
    assert summary.period.pages_pending == 1
    assert summary.pending_count == 1


def test_top_users_excludes_outside_policy(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    ts = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    db_session.add(
        PrintJob(
            printer=fx["allowed"].cups_queue_name,
            printer_id=fx["allowed"].id,
            username="alice",
            job_id=1,
            timestamp=ts,
            pages=1,
            color_mode="mono",
        )
    )
    db_session.add(
        PrintJob(
            printer=fx["other"].cups_queue_name,
            printer_id=fx["other"].id,
            username="alice",
            job_id=2,
            timestamp=ts,
            pages=1,
            color_mode="mono",
        )
    )
    db_session.commit()

    summary = build_summary(db_session, date(2026, 5, 1), date(2026, 5, 31))
    assert summary.period.pages_billable == 1
    names = [t.name for t in summary.top_users]
    assert "Alice" in names
    assert all(t.pages <= 1 for t in summary.top_users)


def test_previous_period_month_vs_rolling() -> None:
    month_prev = previous_period_bounds(
        date(2026, 5, 1), date(2026, 5, 31), preset="month"
    )
    assert month_prev == (date(2026, 4, 1), date(2026, 4, 30))

    rolling_prev = previous_period_bounds(
        date(2026, 5, 2), date(2026, 5, 31), preset="last30"
    )
    assert rolling_prev == (date(2026, 4, 2), date(2026, 5, 1))


def test_delta_pct_pages(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    pid = fx["allowed"].id
    for d, count in ((date(2026, 4, 15), 100), (date(2026, 5, 15), 110)):
        for i in range(count):
            db_session.add(
                PrintJob(
                    printer=fx["allowed"].cups_queue_name,
                    printer_id=pid,
                    username="alice",
                    job_id=d.toordinal() * 10000 + i,
                    timestamp=datetime(
                        d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc
                    ),
                    pages=1,
                    color_mode="mono",
                )
            )
    db_session.commit()

    summary = build_summary(db_session, date(2026, 5, 1), date(2026, 5, 31))
    assert summary.period.pages_billable == 110
    assert summary.period.previous is not None
    assert summary.period.previous.pages_billable == 100
    assert summary.period.delta_pct_pages == 10.0


def test_has_rates_false_without_cost_rate(db_session: Session) -> None:
    summary = build_summary(db_session, date(2026, 5, 1), date(2026, 5, 31))
    assert summary.has_rates is False
    assert summary.period.estimated_cost is None


def test_summary_90d_under_3s(db_session: Session) -> None:
    """ANAL-04 smoke: requer schema com ix_print_jobs_timestamp (alembic upgrade head)."""
    fx = seed_manager_fixtures(db_session)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    pid = fx["allowed"].id
    for i in range(5000):
        db_session.add(
            PrintJob(
                printer=fx["allowed"].cups_queue_name,
                printer_id=pid,
                username="alice",
                job_id=i,
                timestamp=base + timedelta(hours=i % (90 * 24)),
                pages=1,
                color_mode="mono" if i % 3 else "color",
            )
        )
    db_session.commit()

    start = time.perf_counter()
    build_summary(
        db_session,
        date(2026, 1, 1),
        date(2026, 3, 31),
        preset="last90",
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, f"build_summary took {elapsed:.2f}s"


def test_synthetic_bucket_in_top_users(db_session: Session) -> None:
    seed_manager_fixtures(db_session)
    ts = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    db_session.add(
        PrintJob(
            printer="unknown_q",
            printer_id=None,
            username="ghost",
            job_id=1,
            timestamp=ts,
            pages=1,
            color_mode="mono",
        )
    )
    db_session.commit()

    summary = build_summary(db_session, date(2026, 5, 1), date(2026, 5, 31))
    names = [t.name for t in summary.top_users]
    assert BUCKET_UNREGISTERED_USER in names


def test_explain_uses_timestamp_index(db_session: Session) -> None:
    """Valida que filtro por timestamp pode usar índice (SQLite EXPLAIN)."""
    from sqlalchemy import text

    seed_manager_fixtures(db_session)
    db_session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_print_jobs_timestamp "
            "ON print_jobs(timestamp)"
        )
    )
    db_session.commit()
    result = db_session.execute(
        text(
            "EXPLAIN QUERY PLAN SELECT * FROM print_jobs "
            "WHERE timestamp >= '2026-01-01' AND timestamp <= '2026-12-31'"
        )
    ).fetchall()
    plan = " ".join(str(row) for row in result).lower()
    assert "print_jobs" in plan
    assert "index" in plan or "ix_print_jobs_timestamp" in plan


def test_manager_service_no_aggregated_subquery() -> None:
    from pathlib import Path

    text = Path("app/services/manager_service.py").read_text(encoding="utf-8")
    assert "_build_aggregated_subquery" not in text
