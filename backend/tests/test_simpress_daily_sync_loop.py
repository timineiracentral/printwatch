"""Wave 2 RED — D-02 agenda diária às 08:00 America/Sao_Paulo."""
from __future__ import annotations

import asyncio
import importlib
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

_TZ = ZoneInfo("America/Sao_Paulo")


def _daily_sync_loop_module():
    try:
        return importlib.import_module("app.simpress.jobs.daily_sync_loop")
    except ModuleNotFoundError as exc:
        pytest.fail(f"daily_sync_loop não implementado: {exc}")


def _should_run_daily():
    return _daily_sync_loop_module().should_run_daily


def _run_one_loop_iteration(monkeypatch: pytest.MonkeyPatch) -> tuple[list[int], list[int]]:
    """Executa uma iteração do loop; cancela no primeiro sleep."""
    mod = _daily_sync_loop_module()
    sync_calls: list[int] = []
    remind_calls: list[int] = []

    async def fake_run_sync(_db) -> None:
        sync_calls.append(1)

    async def fake_run_remind(_db, **kwargs) -> object:
        remind_calls.append(1)
        return mod.send_pipeline.RemindBatchSummary()

    class FakeDb:
        def close(self) -> None:
            return None

    monkeypatch.setattr(mod.sync_service, "run_sync", fake_run_sync)
    monkeypatch.setattr(mod.sync_service, "is_sync_running", lambda: False)
    monkeypatch.setattr(mod, "_last_local_run_date", lambda _db: None)
    monkeypatch.setattr(mod, "SimpressSessionLocal", FakeDb)
    monkeypatch.setattr(mod.send_pipeline, "run_remind_batch", fake_run_remind)

    cancelled = False

    async def fake_sleep(_seconds: float) -> None:
        nonlocal cancelled
        if not cancelled:
            cancelled = True
            raise asyncio.CancelledError()

    monkeypatch.setattr(mod.asyncio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(mod.daily_sync_loop())

    return sync_calls, remind_calls


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


def test_cad04_daily_tick_chama_run_remind_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _daily_sync_loop_module()
    monkeypatch.setattr(mod, "should_run_daily", lambda _now, _last: True)
    sync_calls, remind_calls = _run_one_loop_iteration(monkeypatch)
    assert len(sync_calls) == 1
    assert len(remind_calls) == 1


def test_cad04_fora_da_janela_nao_chama_remind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _daily_sync_loop_module()
    monkeypatch.setattr(mod, "should_run_daily", lambda _now, _last: False)
    sync_calls, remind_calls = _run_one_loop_iteration(monkeypatch)
    assert sync_calls == []
    assert remind_calls == []


def test_cad04_sync_falha_ainda_chama_remind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _daily_sync_loop_module()
    monkeypatch.setattr(mod, "should_run_daily", lambda _now, _last: True)

    async def failing_sync(_db) -> None:
        raise RuntimeError("sync boom")

    remind_calls: list[int] = []

    async def fake_run_remind(_db, **kwargs) -> object:
        remind_calls.append(1)
        return mod.send_pipeline.RemindBatchSummary()

    class FakeDb:
        def close(self) -> None:
            return None

    monkeypatch.setattr(mod.sync_service, "run_sync", failing_sync)
    monkeypatch.setattr(mod.sync_service, "is_sync_running", lambda: False)
    monkeypatch.setattr(mod, "_last_local_run_date", lambda _db: None)
    monkeypatch.setattr(mod, "SimpressSessionLocal", FakeDb)
    monkeypatch.setattr(mod.send_pipeline, "run_remind_batch", fake_run_remind)

    cancelled = False

    async def fake_sleep(_seconds: float) -> None:
        nonlocal cancelled
        if not cancelled:
            cancelled = True
            raise asyncio.CancelledError()

    monkeypatch.setattr(mod.asyncio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(mod.daily_sync_loop())

    assert len(remind_calls) == 1
