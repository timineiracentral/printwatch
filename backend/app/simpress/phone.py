"""Normalização/validação de telefone Zap (D-16..D-19)."""
from __future__ import annotations

import re

_E164_MAX = 15
_MIN_DIGITS = 10


def normalize_phone(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")


def validate_phone(digits: str) -> str:
    if not digits.isdigit():
        raise ValueError("phone must be digits only after normalize")
    if not (_MIN_DIGITS <= len(digits) <= _E164_MAX):
        raise ValueError("phone length out of range for DDI+DDD number")
    if digits.startswith("0"):
        raise ValueError("phone must include country code (DDI), not leading trunk 0")
    return digits
