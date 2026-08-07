"""Wave 0 RED — CAD-02, D-12/D-14/D-15 via send_pipeline.run_remind_batch."""
from __future__ import annotations

import asyncio
import importlib
from typing import Any

import pytest

from tests.conftest_simpress import FakeZap, PUBLIC_BASE_URL_TEST


def _send_pipeline():
    try:
        return importlib.import_module("app.simpress.services.send_pipeline")
    except ModuleNotFoundError as exc:
        pytest.fail(f"send_pipeline não implementado: {exc}")


def _document_store():
    try:
        return importlib.import_module("app.simpress.services.document_store")
    except ModuleNotFoundError as exc:
        pytest.fail(f"document_store não implementado: {exc}")


def _run_batch(db: Any, zap: FakeZap) -> Any:
    send_pipeline = _send_pipeline()
    return asyncio.run(
        send_pipeline.run_remind_batch(
            db,
            zap_factory=lambda: zap,
        )
    )


def test_d14_zap_offline_aborts_with_zero_sends(
    simpress_session: Any, fake_zap: FakeZap
) -> None:
    fake_zap._connected = False
    summary = _run_batch(simpress_session, fake_zap)

    assert fake_zap.text_calls == []
    assert fake_zap.document_calls == []
    assert summary.aborted is True or summary.sent_count == 0


def test_cad02_sends_text_and_document_per_contact(
    simpress_session: Any, fake_zap: FakeZap
) -> None:
    _run_batch(simpress_session, fake_zap)

    assert fake_zap.text_calls, "deve enviar texto"
    assert fake_zap.document_calls, "deve enviar documento"
    assert len(fake_zap.text_calls) == len(fake_zap.document_calls)


def test_d15_document_url_uses_public_base(
    simpress_session: Any, fake_zap: FakeZap
) -> None:
    _run_batch(simpress_session, fake_zap)

    if not fake_zap.document_calls:
        pytest.fail("document_calls vazio — pipeline não implementado")
    for call in fake_zap.document_calls:
        assert call["url"].startswith(PUBLIC_BASE_URL_TEST.rstrip("/"))


def test_d12_retry_only_missing_part_on_next_run(
    simpress_session: Any,
) -> None:
    zap_first = FakeZap(fail_document=True)
    _run_batch(simpress_session, zap_first)
    text_after_fail = len(zap_first.text_calls)

    zap_retry = FakeZap()
    _run_batch(simpress_session, zap_retry)

    assert len(zap_retry.text_calls) <= text_after_fail
    assert zap_retry.document_calls, "retry deve enviar só documento faltante"


def test_d15_does_not_resend_successful_text_part(
    simpress_session: Any,
) -> None:
    zap_ok = FakeZap()
    _run_batch(simpress_session, zap_ok)
    first_text_count = len(zap_ok.text_calls)

    zap_retry = FakeZap(fail_document=True)
    _run_batch(simpress_session, zap_retry)

    assert len(zap_retry.text_calls) == 0
