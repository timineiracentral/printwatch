"""Testes import CSV meter readings (07-03)."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_manager_service import seed_manager_fixtures


def test_import_partial_errors(client: TestClient, db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    csv_content = (
        "printer_code,counter_total,timestamp,counter_mono,counter_color\n"
        f"{fx['allowed'].cups_queue_name},1000,2026-05-01T08:00:00Z,,\n"
        "unknown_printer,2000,2026-05-02T08:00:00Z,,\n"
    ).encode("utf-8")

    r = client.post(
        "/api/v1/import/meter-readings",
        files={"file": ("readings.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] == 1
    assert len(body["errors"]) == 1


def test_csv_formula_sanitized_on_import(client: TestClient, db_session: Session) -> None:
    fx = seed_manager_fixtures(db_session)
    csv_content = (
        "printer_code,counter_total,timestamp,counter_mono,counter_color\n"
        f"=cmd|'/c calc'!A0,1000,2026-05-01T08:00:00Z,,\n"
        f"{fx['allowed'].cups_queue_name},1100,2026-05-02T08:00:00Z,,\n"
    ).encode("utf-8")

    r = client.post(
        "/api/v1/import/meter-readings",
        files={"file": ("readings.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 200
    assert r.json()["created"] == 1
