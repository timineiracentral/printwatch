"""Wave 2 RED — rota pública ZIP token-only (T-17-04)."""
from __future__ import annotations

import importlib
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest_simpress import DEFAULT_ZIP_BYTES


def _document_store():
    try:
        return importlib.import_module("app.simpress.services.document_store")
    except ModuleNotFoundError as exc:
        pytest.fail(f"document_store não implementado: {exc}")


def _seed_invoice_with_zip(db: Any, docs_path: Path) -> tuple[Any, str]:
    from app.simpress.db.models import Cnpj, Invoice

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cnpj = Cnpj(
        cnpj="11222333000181",
        name="Public Docs",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(cnpj)
    db.flush()
    inv = Invoice(
        cnpj_id=cnpj.id,
        contract_code="CTR001",
        invoice_number="NF-PUB",
        cnpj=cnpj.cnpj,
        status="Vencido",
        amount=Decimal("10.00"),
        zip_token=None,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    token = _document_store().save_zip(db, inv, DEFAULT_ZIP_BYTES)
    db.refresh(inv)
    assert (docs_path / f"{token}.zip").is_file()
    return inv, token


def _pdf_count(root: Path) -> int:
    return len(list(root.rglob("*.pdf")))


def test_get_public_doc_retorna_zip_intacto(
    simpress_client_on: TestClient,
    simpress_session: Any,
    simpress_docs_path: Path,
) -> None:
    _, token = _seed_invoice_with_zip(simpress_session, simpress_docs_path)
    r = simpress_client_on.get(f"/api/v1/simpress/public/docs/{token}")

    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/zip")
    disp = r.headers.get("content-disposition", "")
    assert ".zip" in disp.lower()
    assert r.content == DEFAULT_ZIP_BYTES
    assert _pdf_count(simpress_docs_path) == 0


@pytest.mark.parametrize(
    "bad_token",
    [
        "unknown-token-value",
        "../etc/passwd",
        "token/with/slash",
        "token\\backslash",
    ],
)
def test_token_invalido_ou_traversal_retorna_404(
    simpress_client_on: TestClient,
    simpress_docs_path: Path,
    bad_token: str,
) -> None:
    before = {p.name for p in simpress_docs_path.iterdir()}
    r = simpress_client_on.get(f"/api/v1/simpress/public/docs/{bad_token}")
    assert r.status_code == 404
    after = {p.name for p in simpress_docs_path.iterdir()}
    assert before == after


def test_apos_purge_public_doc_retorna_404(
    simpress_client_on: TestClient,
    simpress_session: Any,
    simpress_docs_path: Path,
) -> None:
    invoice, token = _seed_invoice_with_zip(simpress_session, simpress_docs_path)
    assert simpress_client_on.get(f"/api/v1/simpress/public/docs/{token}").status_code == 200

    _document_store().delete_zip(simpress_session, invoice)
    r = simpress_client_on.get(f"/api/v1/simpress/public/docs/{token}")
    assert r.status_code == 404
    assert _pdf_count(simpress_docs_path) == 0
