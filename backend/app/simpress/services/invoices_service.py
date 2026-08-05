"""Regras de fatura Simpress — upsert, lista aberta, fechamento (SYNC-02)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.simpress.db.models import Invoice
from app.simpress.services import document_store

OPEN_STATUSES = frozenset({"Vencido", "A Vencer"})
CLOSED_STATUSES = frozenset({"Pago", "Cancelado"})


def _utc_now() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        return None


def _normalize_status(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        mapping = {1: "Vencido", 2: "A Vencer", 3: "Pago", 4: "Cancelado"}
        return mapping.get(raw)
    text = str(raw).strip()
    if text in OPEN_STATUSES or text in CLOSED_STATUSES:
        return text
    return None


def _portal_keys(row: dict[str, Any]) -> tuple[str, str]:
    contract = row.get("contrato") or {}
    code = contract.get("codigoContrato")
    nota = row.get("numeroNota")
    if not code or not nota:
        raise ValueError("portal row sem contrato/nota")
    return str(code), str(nota)


def _find_invoice(db: Session, contract_code: str, invoice_number: str) -> Invoice | None:
    return db.scalars(
        select(Invoice).where(
            Invoice.contract_code == contract_code,
            Invoice.invoice_number == invoice_number,
        )
    ).first()


def upsert_open_invoice(db: Session, cnpj_id: int, cnpj_digits: str, row: dict[str, Any]) -> Invoice:
    status = _normalize_status(row.get("statusPagamento"))
    if status not in OPEN_STATUSES:
        raise ValueError("status não aberto")
    contract_code, invoice_number = _portal_keys(row)
    now = _utc_now()
    inv = _find_invoice(db, contract_code, invoice_number)
    amount = Decimal(str(row.get("valor") or 0))
    if inv is None:
        inv = Invoice(
            cnpj_id=cnpj_id,
            contract_code=contract_code,
            invoice_number=invoice_number,
            cnpj=cnpj_digits,
            status=status,
            amount=amount,
            issued_at=_parse_dt(row.get("dataEmissao")),
            due_at=_parse_dt(row.get("dataVencimento")),
            reference=(str(row["referencia"]).strip() if row.get("referencia") else None),
            zip_token=None,
            created_at=now,
            updated_at=now,
        )
        db.add(inv)
    else:
        inv.cnpj_id = cnpj_id
        inv.cnpj = cnpj_digits
        inv.status = status
        inv.amount = amount
        inv.issued_at = _parse_dt(row.get("dataEmissao"))
        inv.due_at = _parse_dt(row.get("dataVencimento"))
        inv.reference = (
            str(row["referencia"]).strip() if row.get("referencia") else None
        )
        inv.updated_at = now
    db.commit()
    db.refresh(inv)
    return inv


def mark_closed_and_purge_zip(db: Session, row: dict[str, Any], status: str) -> Invoice | None:
    if status not in CLOSED_STATUSES:
        raise ValueError("status fechado inválido")
    contract_code, invoice_number = _portal_keys(row)
    inv = _find_invoice(db, contract_code, invoice_number)
    if inv is None:
        return None
    inv.status = status
    inv.updated_at = _utc_now()
    document_store.delete_zip(db, inv)
    db.refresh(inv)
    return inv


def list_open_invoices(db: Session, q: Optional[str] = None) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .where(Invoice.status.in_(tuple(OPEN_STATUSES)))
        .order_by(Invoice.due_at.asc().nullslast(), Invoice.invoice_number.asc())
    )
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Invoice.cnpj.ilike(term), Invoice.invoice_number.ilike(term))
        )
    return list(db.scalars(stmt))
