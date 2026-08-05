"""GET público /api/v1/simpress/public/docs/{token} — ZIP token-only (SYNC-03)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.simpress.db.session import get_simpress_db
from app.simpress.services import document_store

router = APIRouter()


@router.get("/docs/{token}")
def get_public_doc(token: str, db: Session = Depends(get_simpress_db)) -> FileResponse:
    resolved = document_store.resolve_zip_by_token(db, token)
    if resolved is None:
        raise HTTPException(status_code=404, detail="not found")
    invoice, zip_path = resolved
    filename = f"boleto_{invoice.invoice_number}.zip"
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=filename,
    )
