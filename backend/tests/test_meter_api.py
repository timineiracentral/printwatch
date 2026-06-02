"""Testes API meter readings (07-03)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_manager_service import seed_manager_fixtures


def test_create_reading(client: TestClient, db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    r = client.post(
        f"/api/v1/printers/{fx['allowed'].id}/meter-readings",
        json={
            "timestamp": "2026-05-10T12:00:00Z",
            "counter_total": 5000,
            "counter_mono": 3000,
            "counter_color": 2000,
            "source": "manual",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["counter_total"] == 5000


def test_list_history(client: TestClient, db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    pid = fx["allowed"].id
    for day in (1, 15):
        client.post(
            f"/api/v1/printers/{pid}/meter-readings",
            json={
                "timestamp": f"2026-05-{day:02d}T12:00:00Z",
                "counter_total": day * 100,
                "source": "manual",
            },
        )
    r = client.get(f"/api/v1/printers/{pid}/meter-readings")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["counter_total"] == 1500


def test_create_reading_404_unknown_printer(client: TestClient) -> None:
    r = client.post(
        "/api/v1/printers/99999/meter-readings",
        json={
            "timestamp": "2026-05-10T12:00:00Z",
            "counter_total": 1,
            "source": "manual",
        },
    )
    assert r.status_code == 404
