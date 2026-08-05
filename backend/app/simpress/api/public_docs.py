"""GET público token-only para ZIP de boleto (SYNC-03)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.simpress.db.session import get_simpress_db
from app.simpress.services import document_store

router = APIRouter()


@router.get("/docs/{token}")
def get_public_doc(token: str, db: Session = Depends(get_simpress_db)) -> FileResponse:
    path = document_store.resolve_zip_by_token(db, token)
    if path is None:
        raise HTTPException(status_code=404, detail="documento não encontrado")

    from sqlalchemy import select

    from app.simpress.db.models import Invoice

    row = db.scalars(select(Invoice).where(Invoice.zip_token == token)).first()
    nota = row.invoice_number if row else "boleto"
    safe_nota = "".join(c if c.isalnum() or c in "-_" else "_" for c in nota)[:64]
    return FileResponse(
        path,
        media_type="application/zip",
        filename=f"boleto_{safe_nota}.zip",
    )
