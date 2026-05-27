"""Testes API printer-access (05.2-02)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _dept_and_user(client: TestClient) -> tuple[dict, dict]:
    r = client.post(
        "/api/v1/departments", json={"code": "TI", "name": "TI"}
    )
    assert r.status_code == 201
    dept = r.json()
    r = client.post(
        "/api/v1/users",
        json={
            "cups_username": "DOMAIN\\bob",
            "display_name": "Bob",
            "department_id": dept["id"],
        },
    )
    assert r.status_code == 201
    return dept, r.json()


def _printer(client: TestClient, name: str, queue: str) -> dict:
    r = client.post(
        "/api/v1/printers",
        json={"display_name": name, "cups_queue_name": queue},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_replace_assignments_default_unique(client: TestClient) -> None:
    _, user = _dept_and_user(client)
    p1 = _printer(client, "P1", "p1")
    p2 = _printer(client, "P2", "p2")
    r = client.put(
        f"/api/v1/users/{user['id']}/printer-access",
        json={
            "assignments": [
                {"printer_id": p1["id"], "is_default": True},
                {"printer_id": p2["id"], "is_default": True},
            ]
        },
    )
    assert r.status_code == 422


def test_put_three_printers_one_default(client: TestClient) -> None:
    _, user = _dept_and_user(client)
    printers = [_printer(client, f"P{i}", f"q{i}") for i in range(3)]
    body = {
        "assignments": [
            {"printer_id": printers[0]["id"], "is_default": True},
            {"printer_id": printers[1]["id"], "is_default": False},
            {"printer_id": printers[2]["id"], "is_default": False},
        ]
    }
    r = client.put(f"/api/v1/users/{user['id']}/printer-access", json=body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) == 3
    assert sum(1 for row in data if row["is_default"]) == 1


def test_empty_assignments_clears_active(client: TestClient) -> None:
    _, user = _dept_and_user(client)
    p = _printer(client, "Only", "only")
    client.put(
        f"/api/v1/users/{user['id']}/printer-access",
        json={"assignments": [{"printer_id": p["id"], "is_default": True}]},
    )
    r = client.put(
        f"/api/v1/users/{user['id']}/printer-access",
        json={"assignments": []},
    )
    assert r.status_code == 200
    r2 = client.get(f"/api/v1/users/{user['id']}/printer-access")
    assert r2.json() == []


def test_printer_users_read_only_mirror(client: TestClient) -> None:
    _, user = _dept_and_user(client)
    p = _printer(client, "Shared", "shared")
    client.put(
        f"/api/v1/users/{user['id']}/printer-access",
        json={"assignments": [{"printer_id": p["id"], "is_default": True}]},
    )
    r = client.get(f"/api/v1/printers/{p['id']}/users")
    assert r.status_code == 200
    users = r.json()
    assert len(users) == 1
    assert users[0]["id"] == user["id"]
    assert users[0]["is_default"] is True
