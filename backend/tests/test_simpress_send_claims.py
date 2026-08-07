"""Wave 0 RED — CAD-03 UNIQUE send_claims (invoice_id, stage, contact_id, part)."""
from __future__ import annotations

import importlib
from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError

_VALID_CNPJ = "11222333000181"


def _models():
    try:
        return importlib.import_module("app.simpress.db.models")
    except ModuleNotFoundError as exc:
        pytest.fail(f"models SendClaim não implementado: {exc}")


def _claims_service():
    try:
        return importlib.import_module("app.simpress.services.send_claims")
    except ModuleNotFoundError as exc:
        pytest.fail(f"send_claims service não implementado: {exc}")


def _seed_contact(db: Any) -> tuple[Any, Any]:
    from app.simpress.schemas.cnpj import CnpjCreate
    from app.simpress.schemas.contact import ContactCreate
    from app.simpress.services import cnpjs_service, contacts_service, links_service

    cnpj = cnpjs_service.create_cnpj(
        db, CnpjCreate(cnpj=_VALID_CNPJ, name="Empresa Claims")
    )
    contact = contacts_service.create_contact(
        db,
        ContactCreate(name="Contato Teste", phone="5511999990001"),
    )
    links_service.replace_links(db, cnpj.id, [contact.id])
    return cnpj, contact


def _seed_invoice(db: Any, cnpj: Any) -> Any:
    from app.simpress.db.models import Invoice

    inv = Invoice(
        cnpj_id=cnpj.id,
        invoice_number="NF-CLAIM-001",
        amount=100.0,
        status="Vencido",
        reference="08/2026",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def test_cad03_unique_claim_blocks_duplicate_success(
    simpress_session: Any,
) -> None:
    models = _models()
    SendClaim = getattr(models, "SendClaim", None)
    if SendClaim is None:
        pytest.fail("SendClaim model ausente")

    claims = _claims_service()
    cnpj, contact = _seed_contact(simpress_session)
    invoice = _seed_invoice(simpress_session, cnpj)

    claims.record_success(
        simpress_session,
        invoice_id=invoice.id,
        stage="new",
        contact_id=contact.id,
        part="text",
    )
    claims.record_success(
        simpress_session,
        invoice_id=invoice.id,
        stage="new",
        contact_id=contact.id,
        part="text",
    )

    count = claims.count_claims(
        simpress_session,
        invoice_id=invoice.id,
        stage="new",
        contact_id=contact.id,
        part="text",
    )
    assert count == 1


def test_cad03_different_parts_are_independent(
    simpress_session: Any,
) -> None:
    claims = _claims_service()
    cnpj, contact = _seed_contact(simpress_session)
    invoice = _seed_invoice(simpress_session, cnpj)

    claims.record_success(
        simpress_session,
        invoice_id=invoice.id,
        stage="new",
        contact_id=contact.id,
        part="text",
    )
    claims.record_success(
        simpress_session,
        invoice_id=invoice.id,
        stage="new",
        contact_id=contact.id,
        part="document",
    )

    assert claims.count_claims(simpress_session, invoice_id=invoice.id, stage="new") == 2


def test_cad03_integrity_error_on_raw_duplicate_insert(
    simpress_session: Any,
) -> None:
    models = _models()
    SendClaim = getattr(models, "SendClaim", None)
    if SendClaim is None:
        pytest.fail("SendClaim model ausente")

    cnpj, contact = _seed_contact(simpress_session)
    invoice = _seed_invoice(simpress_session, cnpj)

    row = SendClaim(
        invoice_id=invoice.id,
        stage="new",
        contact_id=contact.id,
        part="text",
    )
    simpress_session.add(row)
    simpress_session.commit()

    dup = SendClaim(
        invoice_id=invoice.id,
        stage="new",
        contact_id=contact.id,
        part="text",
    )
    simpress_session.add(dup)
    with pytest.raises(IntegrityError):
        simpress_session.commit()
    simpress_session.rollback()
