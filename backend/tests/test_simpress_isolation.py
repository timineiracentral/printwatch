"""Wave 0 RED stubs — ISO-01 mount/DB boundary."""
from __future__ import annotations

import asyncio
import importlib
import os
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest_simpress import FakePortal, portal_row

_VALID_CNPJ = "11222333000181"


def test_health_200_when_enabled(simpress_client_on: TestClient) -> None:
    r = simpress_client_on.get("/api/v1/simpress/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "status" in body
    assert "db_reachable" in body
    secret_keys = {"password", "api_key", "token", "secret"} & body.keys()
    assert not secret_keys


def test_health_404_when_disabled(simpress_client_off: TestClient) -> None:
    r = simpress_client_off.get("/api/v1/simpress/health")
    assert r.status_code == 404


def test_cnpj_create_does_not_touch_core_print_jobs(
    simpress_client_on: TestClient,
    count_core_rows: Callable[[str], int],
) -> None:
    jobs_before = count_core_rows("print_jobs")
    r = simpress_client_on.post(
        "/api/v1/simpress/cnpjs",
        json={"cnpj": _VALID_CNPJ, "name": "Isolation Test Co"},
    )
    assert r.status_code == 201, r.text
    assert count_core_rows("print_jobs") == jobs_before


def test_sync_fake_nao_altera_print_jobs_nem_core_paths(
    simpress_client_on: TestClient,
    simpress_session,
    simpress_db_path: str,
    simpress_docs_path: Path,
    fake_portal: FakePortal,
    count_core_rows: Callable[[str], int],
) -> None:
    try:
        sync_service = importlib.import_module("app.simpress.services.sync_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"sync_service não implementado: {exc}")

    from app.simpress.schemas.cnpj import CnpjCreate
    from app.simpress.services import cnpjs_service

    cnpjs_service.create_cnpj(
        simpress_session, CnpjCreate(cnpj=_VALID_CNPJ, name="Sync ISO")
    )
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [portal_row(cnpj=_VALID_CNPJ)]

    jobs_before = count_core_rows("print_jobs")
    asyncio.run(
        sync_service.run_sync(
            simpress_session, portal_factory=lambda: fake_portal
        )
    )
    assert count_core_rows("print_jobs") == jobs_before

    assert simpress_db_path.endswith("simpress-pytest.db")
    assert str(simpress_docs_path) == os.environ["SIMPRESS_DOCS_PATH"]
    assert str(simpress_docs_path.parent) in simpress_db_path
    assert not any(simpress_docs_path.rglob("*.pdf"))

