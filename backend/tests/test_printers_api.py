"""Testes CRUD /api/v1/printers (D-11, D-12, D-14, D-18)."""
from __future__ import annotations

import subprocess

from fastapi.testclient import TestClient


def _create(client: TestClient, **overrides) -> dict:
    body = {
        "display_name": "Alpha Lab",
        "cups_queue_name": "alpha",
        **overrides,
    }
    r = client.post("/api/v1/printers", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_list_printers_empty(client: TestClient) -> None:
    r = client.get("/api/v1/printers")
    assert r.status_code == 200
    assert r.json() == []


def test_crud_lifecycle(client: TestClient) -> None:
    created = _create(client)
    assert created["id"] > 0
    assert created["cups_queue_name"] == "alpha"
    assert created["is_active"] is True

    r = client.get(f"/api/v1/printers/{created['id']}")
    assert r.status_code == 200
    assert r.json()["display_name"] == "Alpha Lab"

    r = client.patch(
        f"/api/v1/printers/{created['id']}",
        json={"display_name": "Alpha Updated"},
    )
    assert r.status_code == 200
    assert r.json()["display_name"] == "Alpha Updated"

    r = client.delete(f"/api/v1/printers/{created['id']}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r = client.get("/api/v1/printers")
    assert r.json() == []

    r = client.get("/api/v1/printers", params={"active_only": False})
    assert len(r.json()) == 1
    assert r.json()[0]["is_active"] is False


def test_create_normalizes_cups_queue_name(client: TestClient) -> None:
    created = _create(client, cups_queue_name='"beta"')
    assert created["cups_queue_name"] == "beta"


def test_duplicate_cups_queue_name_409(client: TestClient) -> None:
    _create(client, cups_queue_name="gamma")
    r = client.post(
        "/api/v1/printers",
        json={"display_name": "Other", "cups_queue_name": '"gamma"'},
    )
    assert r.status_code == 409


def test_unmapped_queues(client: TestClient, seed_jobs) -> None:
    r = client.get("/api/v1/printers/unmapped-queues")
    assert r.status_code == 200
    assert set(r.json()) == {"alpha", "beta"}

    _create(client, cups_queue_name="alpha")
    r = client.get("/api/v1/printers/unmapped-queues")
    assert r.status_code == 200
    assert r.json() == ["beta"]


def test_list_printers_does_not_call_cups(
    client: TestClient, seed_jobs, monkeypatch
) -> None:
    """D-21: registry não consulta CUPS via subprocess."""

    def _explode(*args, **kwargs):
        raise AssertionError("endpoint /printers invocou subprocess — D-21 violado")

    monkeypatch.setattr(subprocess, "run", _explode)
    monkeypatch.setattr(subprocess, "check_output", _explode, raising=False)

    r = client.get("/api/v1/printers")
    assert r.status_code == 200
    assert r.json() == []

    r = client.get("/api/v1/printers/unmapped-queues")
    assert r.status_code == 200
    assert "alpha" in r.json()


def test_openapi_lists_printer_paths(client: TestClient) -> None:
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/v1/printers" in paths
    assert "/api/v1/printers/unmapped-queues" in paths
    assert "/api/v1/printers/{printer_id}" in paths
