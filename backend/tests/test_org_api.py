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


def _create_user(client: TestClient, department_id: int, **overrides) -> dict:
    body = {
        "cups_username": "DOMAIN\\alice",
        "display_name": "Alice",
        "department_id": department_id,
        **overrides,
    }
    r = client.post("/api/v1/users", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_users_crud_and_filters(client: TestClient) -> None:
    dept = _create_department(client)
    cc = _create_cost_center(client, code="CC1", name="CC Um")
    user = _create_user(
        client,
        dept["id"],
        cost_center_id=cc["id"],
        cups_username="bob",
        display_name="Bob Silva",
    )
    assert user["cups_username"] == "bob"
    assert user["department_id"] == dept["id"]

    r = client.get("/api/v1/users", params={"department_id": dept["id"]})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get("/api/v1/users", params={"cost_center_id": cc["id"]})
    assert len(r.json()) == 1

    r = client.get("/api/v1/users", params={"q": "silva"})
    assert len(r.json()) == 1

    r = client.get("/api/v1/users", params={"q": "zzz"})
    assert r.json() == []

    r = client.patch(
        f"/api/v1/users/{user['id']}",
        json={"display_name": "Bob Atualizado"},
    )
    assert r.status_code == 200
    assert r.json()["display_name"] == "Bob Atualizado"
    assert r.json()["cups_username"] == "bob"

    r = client.delete(f"/api/v1/users/{user['id']}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_cups_username_immutable_via_schema(client: TestClient) -> None:
    dept = _create_department(client)
    user = _create_user(client, dept["id"], cups_username="carol")
    r = client.patch(
        f"/api/v1/users/{user['id']}",
        json={"cups_username": "hacked", "display_name": "Carol"},
    )
    assert r.status_code == 200
    assert r.json()["cups_username"] == "carol"


def test_duplicate_cups_username_409(client: TestClient) -> None:
    dept = _create_department(client)
    _create_user(client, dept["id"], cups_username="dave")
    r = client.post(
        "/api/v1/users",
        json={
            "cups_username": "dave",
            "display_name": "Dave 2",
            "department_id": dept["id"],
        },
    )
    assert r.status_code == 409


def test_user_requires_active_department(client: TestClient) -> None:
    dept = _create_department(client)
    client.delete(f"/api/v1/departments/{dept['id']}")
    r = client.post(
        "/api/v1/users",
        json={
            "cups_username": "eve",
            "display_name": "Eve",
            "department_id": dept["id"],
        },
    )
    assert r.status_code == 422


def test_openapi_lists_user_list_query_params(client: TestClient) -> None:
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    get_users = r.json()["paths"]["/api/v1/users"]["get"]
    param_names = {p["name"] for p in get_users["parameters"]}
    assert {"department_id", "cost_center_id", "q", "include_inactive"} <= param_names
    assert "/api/v1/departments" in r.json()["paths"]
    assert "/api/v1/cost-centers" in r.json()["paths"]
