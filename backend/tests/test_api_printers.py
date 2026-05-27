"""Testes /api/v1/printers (D-21)."""
from __future__ import annotations

import subprocess

from fastapi.testclient import TestClient


def test_list_printers_empty(client: TestClient) -> None:
    r = client.get("/api/v1/printers")
    assert r.status_code == 200
    assert r.json() == []


def test_list_printers_distinct_sorted(
    client: TestClient, seed_jobs
) -> None:
    r = client.get("/api/v1/printers")
    assert r.status_code == 200
    assert r.json() == ["alpha", "beta"]


def test_list_printers_does_not_call_cups(
    client: TestClient, seed_jobs, monkeypatch
) -> None:
    """D-21: endpoint não pode invocar subprocess para conversar com CUPS."""

    def _explode(*args, **kwargs):
        raise AssertionError(
            "endpoint /printers invocou subprocess — D-21 violado"
        )

    monkeypatch.setattr(subprocess, "run", _explode)
    monkeypatch.setattr(subprocess, "check_output", _explode, raising=False)

    r = client.get("/api/v1/printers")
    assert r.status_code == 200
    assert "alpha" in r.json()
