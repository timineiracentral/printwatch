"""Testes chargeback_export — buckets, outside_policy, rotas (06-04)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import CostRate, Department, PrintJob, Printer, User, UserPrinterAccess
from app.services.chargeback_export import (
    count_chargeback_groups,
    iter_chargeback_csv,
    resolve_chargeback_dates,
)
from app.services.cost_service import (
    BUCKET_UNREGISTERED_PRINTER,
    BUCKET_UNREGISTERED_USER,
    aggregate_cost_by_dimension,
)
from app.schemas.jobs import JobFilters


def _add_rate(db: Session) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)
    db.add(
        CostRate(
            rate_mono=Decimal("0.10"),
            rate_color=Decimal("0.40"),
            valid_from=now,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()


def _seed_dept_user_printer(db: Session) -> tuple[User, Printer, Printer]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    dept = Department(
        code="TI",
        name="TI",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(dept)
    db.flush()
    user = User(
        cups_username="DOMAIN\\alice",
        display_name="Alice",
        department_id=dept.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    allowed = Printer(
        display_name="Lab",
        cups_queue_name="lab",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    other = Printer(
        display_name="Other",
        cups_queue_name="other",
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
    db.commit()
    return user, allowed, other


def test_outside_policy_job_excluded_from_chargeback(db_session: Session) -> None:
    _add_rate(db_session)
    user, allowed, other = _seed_dept_user_printer(db_session)
    ts = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)

    db_session.add(
        PrintJob(
            printer=allowed.cups_queue_name,
            printer_id=allowed.id,
            username=user.cups_username,
            job_id=1,
            timestamp=ts,
            pages=1,
            color_mode="mono",
        )
    )
    db_session.add(
        PrintJob(
            printer=other.cups_queue_name,
            printer_id=other.id,
            username=user.cups_username,
            job_id=2,
            timestamp=ts,
            pages=1,
            color_mode="mono",
        )
    )
    db_session.commit()

    rows = aggregate_cost_by_dimension(
        db_session,
        date(2026, 5, 1),
        date(2026, 5, 31),
        "department",
    )
    dept_rows = [r for r in rows if not r.get("is_bucket")]
    total_mono = sum(r["pages_mono"] for r in rows)
    assert total_mono == 1
    assert len(dept_rows) == 1
    assert dept_rows[0]["pages_mono"] == 1


def test_unregistered_user_goes_to_bucket(db_session: Session) -> None:
    _add_rate(db_session)
    _, allowed, _ = _seed_dept_user_printer(db_session)
    db_session.add(
        PrintJob(
            printer=allowed.cups_queue_name,
            printer_id=allowed.id,
            username="unknown_user",
            job_id=10,
            timestamp=datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc),
            pages=1,
            color_mode="mono",
        )
    )
    db_session.commit()

    rows = aggregate_cost_by_dimension(
        db_session,
        date(2026, 5, 1),
        date(2026, 5, 31),
        "cost_center",
    )
    bucket = next(r for r in rows if r["group_label"] == BUCKET_UNREGISTERED_USER)
    assert bucket["pages_mono"] == 1
    assert bucket["estimated_cost"] == Decimal("0.10")


def test_null_printer_id_goes_to_unregistered_printer_bucket(
    db_session: Session,
) -> None:
    _add_rate(db_session)
    db_session.add(
        PrintJob(
            printer="ghost",
            printer_id=None,
            username="anyone",
            job_id=20,
            timestamp=datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc),
            pages=1,
            color_mode="color",
        )
    )
    db_session.commit()

    rows = aggregate_cost_by_dimension(
        db_session,
        date(2026, 5, 1),
        date(2026, 5, 31),
        "department",
    )
    bucket = next(
        r for r in rows if r["group_label"] == BUCKET_UNREGISTERED_PRINTER
    )
    assert bucket["pages_color"] == 1
    assert bucket["estimated_cost"] == Decimal("0.40")


def test_iter_chargeback_csv_has_bom_and_header(db_session: Session) -> None:
    lines = list(
        iter_chargeback_csv(
            db_session,
            JobFilters(date_from=date(2026, 5, 1), date_to=date(2026, 5, 31)),
            "cost_center",
        )
    )
    assert lines[0] == "\ufeff"
    assert "Grupo;Páginas mono" in lines[1]


def test_resolve_chargeback_dates_defaults_to_current_month() -> None:
    d_from, d_to = resolve_chargeback_dates(JobFilters())
    assert d_from.day == 1
    assert d_from <= d_to


def test_count_chargeback_groups_matches_rows(db_session: Session) -> None:
    filters = JobFilters(date_from=date(2026, 5, 1), date_to=date(2026, 5, 31))
    n = count_chargeback_groups(db_session, filters, "department")
    rows = aggregate_cost_by_dimension(
        db_session, date(2026, 5, 1), date(2026, 5, 31), "department"
    )
    assert n == len(rows)
