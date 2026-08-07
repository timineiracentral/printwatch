"""Wave 0 RED — D-07/D-08 pacing via send_pipeline + asyncio.sleep monkeypatch."""
from __future__ import annotations

import asyncio
import importlib
from typing import Any

import pytest

from tests.conftest_simpress import FakeZap


def _send_pipeline():
    try:
        return importlib.import_module("app.simpress.services.send_pipeline")
    except ModuleNotFoundError as exc:
        pytest.fail(f"send_pipeline não implementado: {exc}")


@pytest.fixture
def sleep_log(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    calls: list[float] = []

    async def _fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
    return calls


def test_d07_sleep_between_posts_in_20_to_60_seconds(
    simpress_session: Any,
    fake_zap: FakeZap,
    sleep_log: list[float],
) -> None:
    send_pipeline = _send_pipeline()
    asyncio.run(
        send_pipeline.run_remind_batch(
            simpress_session,
            zap_factory=lambda: fake_zap,
        )
    )

    inter_post = [s for s in sleep_log if 20 <= s <= 60]
    assert inter_post, f"esperado sleep 20-60s entre POSTs, got {sleep_log}"


def test_d08_pause_1_to_5_minutes_every_30_posts(
    simpress_session: Any,
    fake_zap: FakeZap,
    sleep_log: list[float],
) -> None:
    send_pipeline = _send_pipeline()
    asyncio.run(
        send_pipeline.run_remind_batch(
            simpress_session,
            zap_factory=lambda: fake_zap,
            min_posts_for_test=31,
        )
    )

    long_pauses = [s for s in sleep_log if 60 <= s <= 300]
    assert long_pauses, f"esperado pausa 1-5min a cada 30 POSTs, got {sleep_log}"
