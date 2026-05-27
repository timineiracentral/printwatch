"""Testes ti-export (05.2-05)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _user_and_printers(client: TestClient) -> tuple[dict, list[dict]]:
    r = client.post(
        "/api/v1/departments", json={"code": "RH", "name": "RH"}
    )
    dept = r.json()
    r = client.post(
        "/api/v1/users",
        json={
            "cups_username": "DOMAIN\\ti",
            "display_name": "TI User",
            "department_id": dept["id"],
        },
    )
    user = r.json()
    printers = []
    for i, q in enumerate(("a", "b")):
        r = client.post(
            "/api/v1/printers",
            json={
                "display_name": f"P{i}",
                "cups_queue_name": q,
                "ip_address": f"192.0.2.{i + 1}",
            },
        )
        printers.append(r.json())
    client.put(
        f"/api/v1/users/{user['id']}/printer-access",
        json={
            "assignments": [
                {"printer_id": printers[0]["id"], "is_default": True},
                {"printer_id": printers[1]["id"], "is_default": False},
            ]
        },
    )
    return user, printers


def test_ti_export_json_two_rows(client: TestClient) -> None:
    user, _ = _user_and_printers(client)
    r = client.get(f"/api/v1/users/{user['id']}/ti-export")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_ti_export_csv_content_type(client: TestClient) -> None:
    user, _ = _user_and_printers(client)
    r = client.get(
        f"/api/v1/users/{user['id']}/ti-export",
        params={"format": "csv"},
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
