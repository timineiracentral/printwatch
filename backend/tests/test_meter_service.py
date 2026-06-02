"""Testes meter_service (07-03)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CostRate, PrinterMeterReading
from app.schemas.meter import MeterReadingCreate
from app.services import meter_service
from app.services.manager_service import build_summary
from tests.test_manager_service import seed_manager_fixtures


def _add_reading(
    db: Session,
    printer_id: int,
    *,
    ts: datetime,
    total: int,
    mono: int | None = None,
    color: int | None = None,
) -> PrinterMeterReading:
    return meter_service.create_reading(
        db,
        printer_id,
        MeterReadingCreate(
            timestamp=ts,
            counter_total=total,
            counter_mono=mono,
            counter_color=color,
            source="manual",
        ),
    )


def test_delta_bounds(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    pid = fx["allowed"].id
    _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 1, 8, 0, 0, tzinfo=timezone.utc),
        total=1000,
        mono=600,
        color=400,
    )
    _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 31, 18, 0, 0, tzinfo=timezone.utc),
        total=1500,
        mono=900,
        color=600,
    )

    from app.services.cost_service import _local_date_to_utc_range

    start_utc, _ = _local_date_to_utc_range(date(2026, 5, 1))
    _, end_utc = _local_date_to_utc_range(date(2026, 5, 31))
    initial, final, _ = meter_service._anchor_readings(
        db_session, pid, start_utc, end_utc
    )
    delta = meter_service.compute_delta(initial, final)
    assert delta is not None
    assert delta.pages_total == 500
    assert delta.pages_mono == 300
    assert delta.pages_color == 200


def test_counter_reset_flag(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    pid = fx["allowed"].id
    a = _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 1, tzinfo=timezone.utc),
        total=2000,
    )
    b = _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 20, tzinfo=timezone.utc),
        total=100,
    )
    delta = meter_service.compute_delta(a, b)
    assert delta is not None
    assert delta.counter_reset is True
    assert delta.pages_total == 0


def test_reconciliation_divergence_flag(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    pid = fx["allowed"].id
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        CostRate(
            rate_mono=Decimal("0.10"),
            rate_color=Decimal("0.40"),
            valid_from=datetime(2026, 1, 1),
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()

    _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 1, tzinfo=timezone.utc),
        total=1000,
    )
    _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 31, tzinfo=timezone.utc),
        total=1110,
    )

    from app.db.models import PrintJob

    for i in range(100):
        db_session.add(
            PrintJob(
                printer=fx["allowed"].cups_queue_name,
                printer_id=pid,
                username="alice",
                job_id=5000 + i,
                timestamp=datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc),
                pages=1,
                color_mode="mono",
            )
        )
    db_session.commit()

    rows = meter_service.build_reconciliation(
        db_session, date(2026, 5, 1), date(2026, 5, 31)
    )
    row = next(r for r in rows if r.printer_id == pid)
    assert row.pages_meter == 110
    assert row.pages_jobs == 100
    assert row.divergence_pct is not None
    assert row.divergence_pct >= meter_service.METER_DIVERGENCE_THRESHOLD_PCT * 100


def test_build_summary_includes_meter_reconciliation(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    pid = fx["allowed"].id
    _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 1, tzinfo=timezone.utc),
        total=100,
    )
    _add_reading(
        db_session,
        pid,
        ts=datetime(2026, 5, 31, tzinfo=timezone.utc),
        total=200,
    )
    summary = build_summary(db_session, date(2026, 5, 1), date(2026, 5, 31))
    assert len(summary.meter_reconciliation) >= 1
    match = [r for r in summary.meter_reconciliation if r.printer_id == pid]
    assert match
    assert match[0].pages_meter == 100


def test_upsert_snmp_reading_same_day_replaces_manual(db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    pid = fx["allowed"].id
    day = datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc)
    meter_service.create_reading(
        db_session,
        pid,
        MeterReadingCreate(
            timestamp=day,
            counter_total=1000,
            source="manual",
        ),
    )
    meter_service.upsert_snmp_reading_same_day(
        db_session, pid, day, 1500, None, None
    )
    rows = list(
        db_session.scalars(
            select(PrinterMeterReading).where(PrinterMeterReading.printer_id == pid)
        ).all()
    )
    snmp_rows = [r for r in rows if r.source == "snmp"]
    manual_rows = [r for r in rows if r.source == "manual"]
    assert len(snmp_rows) == 1
    assert snmp_rows[0].counter_total == 1500
    assert manual_rows == []


def test_no_pysnmp_poll_in_meter_service() -> None:
    from pathlib import Path

    text = Path("app/services/meter_service.py").read_text(encoding="utf-8").lower()
    assert "pysnmp" not in text
    assert "snmp_get" not in text
