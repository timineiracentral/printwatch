"""Wave 0 RED — CAD-01/CAD-04, D-01..D-05 via cadence_service.next_due_stage."""
from __future__ import annotations

import importlib
from datetime import date
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

_TZ = ZoneInfo("America/Sao_Paulo")


def _cadence_service():
    try:
        return importlib.import_module("app.simpress.services.cadence_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"cadence_service não implementado: {exc}")


def _invoice(
    *,
    status: str = "Vencido",
    reminder_stage: str = "new",
    launch_date: date | None = date(2026, 8, 1),
    due_date: date | None = date(2026, 8, 15),
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        reminder_stage=reminder_stage,
        launch_date=launch_date,
        due_date=due_date,
    )


def test_d01_launch_day_returns_new() -> None:
    next_due_stage = _cadence_service().next_due_stage
    today = date(2026, 8, 1)
    invoice = _invoice(launch_date=date(2026, 8, 1), reminder_stage="new")
    assert next_due_stage(invoice, today=today) == "new"


def test_d02_stays_in_new_until_plus_five() -> None:
    next_due_stage = _cadence_service().next_due_stage
    today = date(2026, 8, 4)
    invoice = _invoice(launch_date=date(2026, 8, 1), reminder_stage="new")
    assert next_due_stage(invoice, today=today) is None


def test_d03_reminded_5d_on_launch_plus_five() -> None:
    next_due_stage = _cadence_service().next_due_stage
    today = date(2026, 8, 6)
    invoice = _invoice(launch_date=date(2026, 8, 1), reminder_stage="new")
    assert next_due_stage(invoice, today=today) == "reminded_5d"


def test_d03_reminded_10d_on_launch_plus_ten() -> None:
    next_due_stage = _cadence_service().next_due_stage
    today = date(2026, 8, 11)
    invoice = _invoice(
        launch_date=date(2026, 8, 1),
        reminder_stage="reminded_5d",
    )
    assert next_due_stage(invoice, today=today) == "reminded_10d"


def test_d04_overdue_only_after_reminded_10d_and_past_due() -> None:
    next_due_stage = _cadence_service().next_due_stage
    today = date(2026, 8, 20)
    invoice = _invoice(
        launch_date=date(2026, 8, 1),
        reminder_stage="reminded_10d",
        due_date=date(2026, 8, 15),
    )
    assert next_due_stage(invoice, today=today) == "overdue_urgent"


def test_d04_never_skips_stages_before_overdue() -> None:
    next_due_stage = _cadence_service().next_due_stage
    today = date(2026, 8, 20)
    invoice = _invoice(
        launch_date=date(2026, 8, 1),
        reminder_stage="new",
        due_date=date(2026, 8, 10),
    )
    assert next_due_stage(invoice, today=today) != "overdue_urgent"


def test_d05_paid_returns_none() -> None:
    next_due_stage = _cadence_service().next_due_stage
    invoice = _invoice(status="Pago")
    assert next_due_stage(invoice, today=date(2026, 8, 1)) is None


def test_d05_cancelled_returns_none() -> None:
    next_due_stage = _cadence_service().next_due_stage
    invoice = _invoice(status="Cancelado")
    assert next_due_stage(invoice, today=date(2026, 8, 1)) is None
