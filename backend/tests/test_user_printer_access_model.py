"""Smoke tests — modelo e schemas user_printer_access (05.2-01)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.db.models import UserPrinterAccess
from app.schemas.user_printer_access import PrinterAccessReplace


def test_user_printer_access_model_registered() -> None:
    assert UserPrinterAccess.__tablename__ == "user_printer_access"


def test_printer_access_replace_rejects_more_than_50() -> None:
    items = [{"printer_id": i, "is_default": False} for i in range(51)]
    with pytest.raises(ValidationError):
        PrinterAccessReplace(assignments=items)
