"""Testes cost_service — vigência, line_cost, agregação (06-02)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.db.models import CostRate, PrintJob
from app.services.cost_service import (
    BUCKET_PENDING_PAGES,
    aggregate_cost_by_dimension,
    line_cost,
    rate_at,
)


def _add_rate(
    db: Session,
    *,
    mono: str,
    color: str,
    valid_from: datetime,
) -> CostRate:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)
    row = CostRate(
        rate_mono=Decimal(mono),
        rate_color=Decimal(color),
        valid_from=valid_from.replace(tzinfo=None)
        if valid_from.tzinfo
        else valid_from,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    return row


def test_rate_at_uses_older_vigencia_when_event_before_new_rate(db_session: Session) -> None:
    _add_rate(
        db_session,
        mono="0.10",
        color="0.50",
        valid_from=datetime(2024, 1, 1),
    )
    _add_rate(
        db_session,
        mono="0.20",
        color="0.80",
        valid_from=datetime(2024, 6, 1),
    )

    old = rate_at(db_session, datetime(2024, 3, 15))
    assert old is not None
    assert old.rate_mono == Decimal("0.10")

    new = rate_at(db_session, datetime(2024, 7, 1))
    assert new is not None
    assert new.rate_mono == Decimal("0.20")


def test_rate_at_none_without_configured_rates(db_session: Session) -> None:
    assert rate_at(db_session, datetime(2024, 1, 1)) is None
    assert line_cost(None, "mono") is None


def test_line_cost_mono_and_color(db_session: Session) -> None:
    rate = _add_rate(
        db_session,
        mono="0.05",
        color="0.25",
        valid_from=datetime(2026, 1, 1),
    )
    assert line_cost(rate, "mono") == Decimal("0.05")
    assert line_cost(rate, "color") == Decimal("0.25")
    assert line_cost(rate, "unknown") is None
    assert line_cost(rate, None) is None


def test_aggregate_pending_null_color_mode(db_session: Session) -> None:
    _add_rate(
        db_session,
        mono="0.10",
        color="0.40",
        valid_from=datetime(2026, 1, 1),
    )
    db_session.add(
        PrintJob(
            printer="p1",
            printer_id=99,
            username="alice",
            job_id=1,
            timestamp=datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
            pages=1,
            color_mode="mono",
        )
    )
    db_session.add(
        PrintJob(
            printer="p1",
            printer_id=99,
            username="alice",
            job_id=1,
            timestamp=datetime(2026, 5, 10, 12, 0, 1, tzinfo=timezone.utc),
            pages=1,
            color_mode=None,
        )
    )
    db_session.commit()

    rows = aggregate_cost_by_dimension(
        db_session,
        date(2026, 5, 1),
        date(2026, 5, 31),
        "department",
    )
    pending = next(r for r in rows if r["group_label"] == BUCKET_PENDING_PAGES)
    assert pending["pages_pending"] == 1
    assert pending["pages_mono"] == 0
    assert pending["pages_color"] == 0

    unreg = next(
        r for r in rows if r["group_label"] == "Usuário não cadastrado"
    )
    assert unreg["pages_mono"] == 1
    assert unreg["estimated_cost"] == Decimal("0.10")
