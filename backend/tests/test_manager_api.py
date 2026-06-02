"""Testes /api/v1/manager/summary (07-02)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import CostRate, PrintJob
from tests.test_manager_service import seed_manager_fixtures


def test_manager_summary_endpoint(client: TestClient, db_session: Session) -> None:
    seed_manager_fixtures(db_session)
    ts = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    db_session.add(
        PrintJob(
            printer="lab_a",
            printer_id=1,
            username="alice",
            job_id=1,
            timestamp=ts,
            pages=1,
            color_mode="mono",
        )
    )
    db_session.commit()

    r = client.get(
        "/api/v1/manager/summary",
        params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) >= {
        "period",
        "top_users",
        "top_printers",
        "top_departments",
        "meter_reconciliation",
        "has_rates",
    }
    assert body["period"]["pages_billable"] == 0


def test_manager_summary_invalid_date_range(client: TestClient) -> None:
    r = client.get(
        "/api/v1/manager/summary",
        params={"date_from": "2026-02-01", "date_to": "2026-01-01"},
    )
    assert r.status_code == 422


def test_manager_summary_endpoint_in_openapi(client: TestClient) -> None:
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert "/api/v1/manager/summary" in paths


def test_manager_summary_with_data(client: TestClient, db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    ts = datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc)
    db_session.add(
        PrintJob(
            printer=fx["allowed"].cups_queue_name,
            printer_id=fx["allowed"].id,
            username="alice",
            job_id=1,
            timestamp=ts,
            pages=1,
            color_mode="color",
        )
    )
    db_session.commit()

    r = client.get(
        "/api/v1/manager/summary",
        params={"date_from": "2026-05-01", "date_to": "2026-05-31"},
    )
    assert r.status_code == 200
    assert r.json()["period"]["pages_color"] == 1
    assert r.json()["has_rates"] is True
