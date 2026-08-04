"""Wave 0 RED stubs — ISO-01 mount/DB boundary."""
from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient


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
        json={"cnpj": "11222333000181", "name": "Isolation Test Co"},
    )
    assert r.status_code == 201, r.text
    assert count_core_rows("print_jobs") == jobs_before
