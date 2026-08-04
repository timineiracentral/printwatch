"""Wave 0 RED stubs — CNPJ-01/02 CRUD, N:N links, soft-delete."""
from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

_VALID_CNPJ = "11222333000181"
_VALID_PHONE = "5531999999999"


def _create_cnpj(client: TestClient, **overrides) -> dict:
    body = {"cnpj": _VALID_CNPJ, "name": "Empresa Teste", **overrides}
    r = client.post("/api/v1/simpress/cnpjs", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _create_contact(client: TestClient, **overrides) -> dict:
    body = {"name": "Contato Teste", "phone": _VALID_PHONE, **overrides}
    r = client.post("/api/v1/simpress/contacts", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_cnpj_crud_and_soft_delete_excludes_from_default_list(
    simpress_client_on: TestClient,
) -> None:
    created = _create_cnpj(simpress_client_on)
    cnpj_id = created["id"]

    r = simpress_client_on.get("/api/v1/simpress/cnpjs")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = simpress_client_on.patch(
        f"/api/v1/simpress/cnpjs/{cnpj_id}",
        json={"name": "Empresa Atualizada"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Empresa Atualizada"

    r = simpress_client_on.delete(f"/api/v1/simpress/cnpjs/{cnpj_id}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r = simpress_client_on.get("/api/v1/simpress/cnpjs")
    assert r.json() == []

    r = simpress_client_on.get(
        "/api/v1/simpress/cnpjs", params={"include_inactive": True}
    )
    assert len(r.json()) == 1


def test_contact_create_stores_digits_only_phone(simpress_client_on: TestClient) -> None:
    r = simpress_client_on.post(
        "/api/v1/simpress/contacts",
        json={"name": "Zap User", "phone": "+55 31 99999-9999"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["phone"] == _VALID_PHONE


def test_duplicate_phones_allowed_across_contacts(simpress_client_on: TestClient) -> None:
    _create_contact(simpress_client_on, name="A")
    r = simpress_client_on.post(
        "/api/v1/simpress/contacts",
        json={"name": "B", "phone": _VALID_PHONE},
    )
    assert r.status_code == 201, r.text


def test_put_cnpj_contacts_replace_and_empty_allowed(
    simpress_client_on: TestClient,
) -> None:
    cnpj = _create_cnpj(simpress_client_on)
    c1 = _create_contact(simpress_client_on, name="C1")
    c2 = _create_contact(simpress_client_on, name="C2", phone="5531888888888")

    r = simpress_client_on.put(
        f"/api/v1/simpress/cnpjs/{cnpj['id']}/contacts",
        json={"contact_ids": [c1["id"], c2["id"]]},
    )
    assert r.status_code == 200, r.text
    assert len(r.json()) == 2

    r = simpress_client_on.put(
        f"/api/v1/simpress/cnpjs/{cnpj['id']}/contacts",
        json={"contact_ids": []},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_put_contact_cnpjs_replace(simpress_client_on: TestClient) -> None:
    contact = _create_contact(simpress_client_on)
    cnpj = _create_cnpj(simpress_client_on, cnpj="11444777000161", name="Outra")

    r = simpress_client_on.put(
        f"/api/v1/simpress/contacts/{contact['id']}/cnpjs",
        json={"cnpj_ids": [cnpj["id"]]},
    )
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1


def test_soft_delete_cnpj_deactivates_links_shared_contact_remains(
    simpress_client_on: TestClient,
) -> None:
    cnpj_a = _create_cnpj(simpress_client_on)
    cnpj_b = _create_cnpj(simpress_client_on, cnpj="11444777000161", name="B")
    contact = _create_contact(simpress_client_on)

    simpress_client_on.put(
        f"/api/v1/simpress/cnpjs/{cnpj_a['id']}/contacts",
        json={"contact_ids": [contact["id"]]},
    )
    simpress_client_on.put(
        f"/api/v1/simpress/cnpjs/{cnpj_b['id']}/contacts",
        json={"contact_ids": [contact["id"]]},
    )

    simpress_client_on.delete(f"/api/v1/simpress/cnpjs/{cnpj_a['id']}")

    r = simpress_client_on.get("/api/v1/simpress/contacts")
    assert r.status_code == 200
    assert any(c["id"] == contact["id"] for c in r.json())

    r = simpress_client_on.get(
        f"/api/v1/simpress/cnpjs/{cnpj_b['id']}/contacts"
    )
    assert r.status_code == 200
    assert any(link["id"] == contact["id"] for link in r.json())


def test_contact_create_does_not_insert_core_users_or_departments(
    simpress_client_on: TestClient,
    count_core_rows: Callable[[str], int],
) -> None:
    users_before = count_core_rows("users")
    depts_before = count_core_rows("departments")

    _create_contact(simpress_client_on)

    assert count_core_rows("users") == users_before
    assert count_core_rows("departments") == depts_before
