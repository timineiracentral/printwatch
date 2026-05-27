"""Testes API /api/v1/cost-rates (06-02)."""
from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient


def test_cost_rates_crud_and_history(client: TestClient) -> None:
    r = client.get("/api/v1/cost-rates/current")
    assert r.status_code == 404

    r = client.post(
        "/api/v1/cost-rates",
        json={"rate_mono": "0.05", "rate_color": "0.25"},
    )
    assert r.status_code == 201, r.text
    first = r.json()
    assert first["rate_mono"] == "0.0500"
    assert first["rate_color"] == "0.2500"
    assert "valid_from" in first

    r = client.get("/api/v1/cost-rates/current")
    assert r.status_code == 200
    assert r.json()["id"] == first["id"]

    r = client.post(
        "/api/v1/cost-rates",
        json={
            "rate_mono": "0.08",
            "rate_color": "0.30",
            "valid_from": "2025-01-01T00:00:00",
        },
    )
    assert r.status_code == 201

    r = client.get("/api/v1/cost-rates")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 2
    assert items[0]["id"] != items[1]["id"]
