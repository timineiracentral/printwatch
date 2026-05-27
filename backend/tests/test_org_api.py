"""Testes CRUD /api/v1/departments, /cost-centers, /users (D-15–17)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _create_cost_center(client: TestClient, **overrides) -> dict:
    body = {"code": "FIN", "name": "Financeiro", **overrides}
    r = client.post("/api/v1/cost-centers", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _create_department(client: TestClient, **overrides) -> dict:
    body = {"code": "TI", "name": "Tecnologia", **overrides}
    r = client.post("/api/v1/departments", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_cost_center_normalizes_code(client: TestClient) -> None:
    r = client.post(
        "/api/v1/cost-centers",
        json={"code": "fin", "name": "Financeiro"},
    )
    assert r.status_code == 201
    assert r.json()["code"] == "FIN"


def test_duplicate_cost_center_code_409(client: TestClient) -> None:
    _create_cost_center(client, code="OPS")
    r = client.post(
        "/api/v1/cost-centers",
        json={"code": "ops", "name": "Outro"},
    )
    assert r.status_code == 409


def test_cost_centers_list_and_soft_delete(client: TestClient) -> None:
    created = _create_cost_center(client)
    r = client.get("/api/v1/cost-centers")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.delete(f"/api/v1/cost-centers/{created['id']}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r = client.get("/api/v1/cost-centers")
    assert r.json() == []

    r = client.get("/api/v1/cost-centers", params={"include_inactive": True})
    assert len(r.json()) == 1


def test_departments_crud_with_cost_center(client: TestClient) -> None:
    cc = _create_cost_center(client)
    dept = _create_department(client, cost_center_id=cc["id"])
    assert dept["cost_center_id"] == cc["id"]
    assert dept["code"] == "TI"

    r = client.get(f"/api/v1/departments/{dept['id']}")
    assert r.status_code == 200

    r = client.patch(
        f"/api/v1/departments/{dept['id']}",
        json={"name": "TI Atualizado"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "TI Atualizado"


def test_department_rejects_inactive_cost_center(client: TestClient) -> None:
    cc = _create_cost_center(client)
    client.delete(f"/api/v1/cost-centers/{cc['id']}")
    r = client.post(
        "/api/v1/departments",
        json={"code": "RH", "name": "RH", "cost_center_id": cc["id"]},
    )
    assert r.status_code == 422


def test_duplicate_department_code_409(client: TestClient) -> None:
    _create_department(client, code="ADM")
    r = client.post(
        "/api/v1/departments",
        json={"code": "adm", "name": "Admin 2"},
    )
    assert r.status_code == 409
