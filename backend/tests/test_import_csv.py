"""Testes import CSV bulk (D-23–D-26)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _create_department(client: TestClient, **overrides) -> dict:
    body = {"code": "TI", "name": "Tecnologia", **overrides}
    r = client.post("/api/v1/departments", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_download_users_template(client: TestClient) -> None:
    r = client.get("/api/v1/import/templates/users")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert r.headers.get("content-disposition", "").startswith("attachment")
    header = r.text.strip().splitlines()[0]
    assert header == "cups_username,display_name,department_code,cost_center_code"


def test_import_users_partial_commit(client: TestClient) -> None:
    _create_department(client)

    lines = ["cups_username,display_name,department_code,cost_center_code"]
    for i in range(48):
        lines.append(f"user{i},User {i},TI,")
    lines.append(",Missing username,TI,")
    lines.append("user99,,TI,")

    csv_content = "\n".join(lines)
    r = client.post(
        "/api/v1/import/users",
        files={"file": ("users.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total"] == 50
    assert data["created"] == 48
    assert len(data["errors"]) == 2
    assert {e["line"] for e in data["errors"]} == {50, 51}

    users = client.get("/api/v1/users")
    assert users.status_code == 200
    assert len(users.json()) == 48


def test_import_users_strict_rollback(client: TestClient) -> None:
    _create_department(client)

    csv_content = "\n".join(
        [
            "cups_username,display_name,department_code,cost_center_code",
            "alice,Alice Silva,TI,",
            ",Bob Invalid,TI,",
            "carol,Carol Silva,TI,",
        ]
    )
    r = client.post(
        "/api/v1/import/users?strict=true",
        files={"file": ("users.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["created"] == 0
    assert data["updated"] == 0
    assert len(data["errors"]) == 1

    users = client.get("/api/v1/users")
    assert users.status_code == 200
    assert len(users.json()) == 0


def test_import_departments_normalizes_code(client: TestClient) -> None:
    csv_content = "code,name,cost_center_code\nti-low,Tecnologia,\n"
    r = client.post(
        "/api/v1/import/departments",
        files={"file": ("departments.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 1

    dept = client.get("/api/v1/departments").json()[0]
    assert dept["code"] == "TI-LOW"


def test_import_rejects_oversized_file(client: TestClient) -> None:
    payload = b"x" * (5 * 1024 * 1024 + 1)
    r = client.post(
        "/api/v1/import/users",
        files={"file": ("big.csv", payload, "text/csv")},
    )
    assert r.status_code == 413
