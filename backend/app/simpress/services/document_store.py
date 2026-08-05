"""Storage ZIP tokenizado para boletos Simpress (SYNC-03, D-07/D-10)."""
from __future__ import annotations

import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.simpress.config import simpress_settings
from app.simpress.db.models import Invoice

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_ZIP_MAGIC = b"PK"


def _docs_root() -> Path:
    root = Path(simpress_settings.docs_path)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _validate_token(token: str) -> bool:
    if not token or len(token) > 64:
        return False
    return _TOKEN_RE.fullmatch(token) is not None


def _zip_path_for_token(token: str) -> Path:
    root = _docs_root().resolve()
    path = (root / f"{token}.zip").resolve()
    if not path.is_relative_to(root):
        raise ValueError("path outside docs root")
    return path


def save_zip(db: Session, invoice: Invoice, raw_zip: bytes) -> str:
    if not raw_zip.startswith(_ZIP_MAGIC):
        raise ValueError("invalid zip bytes")

    if invoice.zip_token and _validate_token(invoice.zip_token):
        existing = _zip_path_for_token(invoice.zip_token)
        if existing.is_file():
            return invoice.zip_token

    token = secrets.token_urlsafe(32)
    zip_path = _zip_path_for_token(token)
    root = _docs_root()

    fd, tmp_name = tempfile.mkstemp(suffix=".zip", dir=root)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw_zip)
        tmp_path.replace(zip_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    invoice.zip_token = token
    invoice.updated_at = _utc_now()
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return token


def delete_zip(db: Session, invoice: Invoice) -> None:
    token = invoice.zip_token
    if token and _validate_token(token):
        try:
            _zip_path_for_token(token).unlink(missing_ok=True)
        except ValueError:
            pass

    invoice.zip_token = None
    invoice.updated_at = _utc_now()
    db.add(invoice)
    db.commit()


def resolve_zip_by_token(db: Session, token: str) -> tuple[Invoice, Path] | None:
    if not _validate_token(token):
        return None

    invoice = db.scalars(select(Invoice).where(Invoice.zip_token == token)).first()
    if invoice is None:
        return None

    try:
        zip_path = _zip_path_for_token(token)
    except ValueError:
        return None

    if not zip_path.is_file():
        return None

    return invoice, zip_path


def public_url(invoice: Invoice) -> str:
    base = (simpress_settings.public_base_url or "").rstrip("/")
    if not base:
        raise ValueError("PUBLIC_BASE_URL is required")
    if not invoice.zip_token:
        raise ValueError("invoice has no zip token")
    return f"{base}/api/v1/simpress/public/docs/{invoice.zip_token}"
