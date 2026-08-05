"""Wave 2 RED — SYNC-04 manual sync, status, diagnóstico (D-01/D-12/D-14)."""
from __future__ import annotations

import json
import re
import threading
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest_simpress import FakePortal, portal_row

_FORBIDDEN = re.compile(r"(password|api_key|zip_token|public_url|public\.example)", re.I)
_VALID_CNPJ = "11222333000181"


def _create_cnpj(client: TestClient) -> dict:
    r = client.post(
        "/api/v1/simpress/cnpjs",
        json={"cnpj": _VALID_CNPJ, "name": "Sync API Co"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_get_last_sync_404_antes_do_primeiro_run(simpress_client_on: TestClient) -> None:
    r = simpress_client_on.get("/api/v1/simpress/sync/last")
    assert r.status_code == 404


def test_post_sync_inicia_background_com_202(simpress_client_on: TestClient) -> None:
    _create_cnpj(simpress_client_on)
    r = simpress_client_on.post("/api/v1/simpress/sync")
    assert r.status_code == 202, r.text


def test_get_sync_status_reflete_in_progress(
    simpress_client_on: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _create_cnpj(simpress_client_on)
    gate = threading.Event()

    class SlowPortal(FakePortal):
        async def list_invoices(self, **kwargs: Any) -> tuple[list[dict], int]:
            gate.wait(timeout=5)
            return await super().list_invoices(**kwargs)

    slow = SlowPortal(
        rows_by_cnpj={
            _VALID_CNPJ: [portal_row(cnpj=_VALID_CNPJ)],
        }
    )

    def _factory() -> SlowPortal:
        return slow

    monkeypatch.setattr(
        "app.simpress.services.sync_service._default_portal_factory",
        _factory,
        raising=False,
    )
    monkeypatch.setattr(
        "app.simpress.services.sync_service.SimpressPortalClient",
        _factory,
        raising=False,
    )

    r = simpress_client_on.post("/api/v1/simpress/sync")
    assert r.status_code == 202, r.text

    try:
        status = simpress_client_on.get("/api/v1/simpress/sync/status")
        assert status.status_code == 200, status.text
        assert status.json()["in_progress"] is True
    finally:
        gate.set()
        time.sleep(0.3)


def test_segundo_post_durante_sync_retorna_409(
    simpress_client_on: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _create_cnpj(simpress_client_on)
    gate = threading.Event()

    class SlowPortal(FakePortal):
        async def list_invoices(self, **kwargs: Any) -> tuple[list[dict], int]:
            gate.wait(timeout=5)
            return await super().list_invoices(**kwargs)

    slow = SlowPortal(
        rows_by_cnpj={
            _VALID_CNPJ: [portal_row(cnpj=_VALID_CNPJ)],
        }
    )

    def _factory() -> SlowPortal:
        return slow

    monkeypatch.setattr(
        "app.simpress.services.sync_service._default_portal_factory",
        _factory,
        raising=False,
    )
    monkeypatch.setattr(
        "app.simpress.services.sync_service.SimpressPortalClient",
        _factory,
        raising=False,
    )

    first = simpress_client_on.post("/api/v1/simpress/sync")
    assert first.status_code == 202, first.text

    try:
        second = simpress_client_on.post("/api/v1/simpress/sync")
        assert second.status_code == 409, second.text
        assert second.json()["detail"] == "sync em andamento"
    finally:
        gate.set()
        time.sleep(0.3)


def test_get_last_sync_resumo_operacional_sem_segredos(
    simpress_client_on: TestClient,
) -> None:
    _create_cnpj(simpress_client_on)
    started = simpress_client_on.post("/api/v1/simpress/sync")
    assert started.status_code == 202, started.text

    deadline = time.time() + 10
    last_body: dict | None = None
    while time.time() < deadline:
        r = simpress_client_on.get("/api/v1/simpress/sync/last")
        if r.status_code == 200:
            last_body = r.json()
            if last_body.get("finished_at") is not None:
                break
        time.sleep(0.2)

    assert last_body is not None, "último sync não materializou resumo"
    expected_keys = {
        "started_at",
        "finished_at",
        "ok",
        "contracts_count",
        "contract_codes",
        "invoices_upserted",
        "zips_downloaded",
        "cnpj_warnings",
        "errors",
    }
    assert expected_keys <= set(last_body.keys())
    blob = json.dumps(last_body, ensure_ascii=False)
    assert not _FORBIDDEN.search(blob)
    assert len(last_body.get("errors") or []) <= 5
