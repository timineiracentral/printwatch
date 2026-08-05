"""API listagem de faturas abertas (SYNC-02)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.simpress.db.session import get_simpress_db
from app.simpress.schemas.invoice import InvoiceRead
from app.simpress.services import invoices_service

router = APIRouter()


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_simpress_db),
) -> list[InvoiceRead]:
    rows = invoices_service.list_open_invoices(db, q=q)
    return [
        InvoiceRead(
            id=row.id,
            cnpj=row.cnpj,
            invoice_number=row.invoice_number,
            status=row.status,
            amount=row.amount,
            issued_at=row.issued_at,
            due_at=row.due_at,
            reference=row.reference,
            has_zip=row.zip_token is not None,
        )
        for row in rows
    ]
