"""Wave 2 RED — D-02 agenda diária às 08:00 America/Sao_Paulo."""
from __future__ import annotations

import importlib
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

_TZ = ZoneInfo("America/Sao_Paulo")


def _should_run_daily():
    try:
        mod = importlib.import_module("app.simpress.jobs.daily_sync_loop")
    except ModuleNotFoundError as exc:
        pytest.fail(f"daily_sync_loop não implementado: {exc}")
    return mod.should_run_daily


def test_d02_0759_nao_roda() -> None:
    should_run_daily = _should_run_daily()
    now = datetime(2026, 8, 5, 7, 59, 0, tzinfo=_TZ)
    assert should_run_daily(now, last_run_date=None) is False


def test_d02_primeiro_poll_0800_roda() -> None:
    should_run_daily = _should_run_daily()
    now = datetime(2026, 8, 5, 8, 0, 0, tzinfo=_TZ)
    assert should_run_daily(now, last_run_date=None) is True


def test_d02_mesmo_dia_apos_run_nao_duplica() -> None:
    should_run_daily = _should_run_daily()
    now = datetime(2026, 8, 5, 12, 30, 0, tzinfo=_TZ)
    assert should_run_daily(now, last_run_date=date(2026, 8, 5)) is False


def test_d02_novo_dia_roda_novamente() -> None:
    should_run_daily = _should_run_daily()
    now = datetime(2026, 8, 6, 8, 1, 0, tzinfo=_TZ)
    assert should_run_daily(now, last_run_date=date(2026, 8, 5)) is True
