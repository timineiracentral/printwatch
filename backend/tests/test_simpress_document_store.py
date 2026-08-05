"""Wave 2 RED — SYNC-03 token/ZIP lifecycle (D-07/D-10)."""
from __future__ import annotations

import importlib
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from tests.conftest_simpress import DEFAULT_ZIP_BYTES, PUBLIC_BASE_URL_TEST

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _document_store():
    try:
        return importlib.import_module("app.simpress.services.document_store")
    except ModuleNotFoundError as exc:
        pytest.fail(f"document_store não implementado: {exc}")


def _make_invoice(db: Any, *, nota: str = "NF-STORE") -> Any:
    from app.simpress.db.models import Cnpj, Invoice

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cnpj = Cnpj(
        cnpj="11222333000181",
        name="Store Test",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(cnpj)
    db.flush()
    inv = Invoice(
        cnpj_id=cnpj.id,
        contract_code="CTR001",
        invoice_number=nota,
        cnpj=cnpj.cnpj,
        status="Vencido",
        amount=Decimal("99.90"),
        zip_token=None,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _pdf_count(root: Path) -> int:
    return len(list(root.rglob("*.pdf")))


def test_save_zip_cria_arquivo_token_url_e_public_url(
    simpress_session: Any, simpress_docs_path: Path
) -> None:
    document_store = _document_store()
    invoice = _make_invoice(simpress_session)

    token = document_store.save_zip(simpress_session, invoice, DEFAULT_ZIP_BYTES)
    simpress_session.refresh(invoice)

    assert token == invoice.zip_token
    assert token is not None
    assert len(token) >= 43
    assert _TOKEN_RE.fullmatch(token)
    zip_path = simpress_docs_path / f"{token}.zip"
    assert zip_path.is_file()
    assert zip_path.read_bytes() == DEFAULT_ZIP_BYTES
    assert zip_path.name == f"{token}.zip"

    url = document_store.public_url(invoice)
    assert url == f"{PUBLIC_BASE_URL_TEST}/api/v1/simpress/public/docs/{token}"
    assert _pdf_count(simpress_docs_path) == 0


def test_save_repetido_mantem_token_e_bytes(
    simpress_session: Any, simpress_docs_path: Path
) -> None:
    document_store = _document_store()
    invoice = _make_invoice(simpress_session, nota="NF-IDEM")

    first = document_store.save_zip(simpress_session, invoice, DEFAULT_ZIP_BYTES)
    second = document_store.save_zip(simpress_session, invoice, DEFAULT_ZIP_BYTES)
    simpress_session.refresh(invoice)

    assert first == second == invoice.zip_token
    assert len(list(simpress_docs_path.glob("*.zip"))) == 1
    assert (simpress_docs_path / f"{first}.zip").read_bytes() == DEFAULT_ZIP_BYTES


def test_purge_remove_arquivo_e_token(
    simpress_session: Any, simpress_docs_path: Path
) -> None:
    document_store = _document_store()
    invoice = _make_invoice(simpress_session, nota="NF-PURGE")
    token = document_store.save_zip(simpress_session, invoice, DEFAULT_ZIP_BYTES)
    zip_path = simpress_docs_path / f"{token}.zip"
    assert zip_path.is_file()

    document_store.delete_zip(simpress_session, invoice)
    simpress_session.refresh(invoice)

    assert invoice.zip_token is None
    assert not zip_path.exists()


def test_novo_save_apos_purge_gera_token_diferente(
    simpress_session: Any, simpress_docs_path: Path
) -> None:
    document_store = _document_store()
    invoice = _make_invoice(simpress_session, nota="NF-NEW-TOK")
    old = document_store.save_zip(simpress_session, invoice, DEFAULT_ZIP_BYTES)
    document_store.delete_zip(simpress_session, invoice)

    new = document_store.save_zip(simpress_session, invoice, DEFAULT_ZIP_BYTES)
    simpress_session.refresh(invoice)

    assert new != old
    assert invoice.zip_token == new
    assert (simpress_docs_path / f"{new}.zip").is_file()
    assert not (simpress_docs_path / f"{old}.zip").exists()
