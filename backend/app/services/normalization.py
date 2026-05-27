"""Compat: reexporta normalização de app.core.normalize.

Preferir `from app.core.normalize import normalize_printer_name` em código novo.
"""
from __future__ import annotations

from app.core.normalize import normalize_printer_name

__all__ = ["normalize_printer_name"]
