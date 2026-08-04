"""Normalização/validação CNPJ numérico clássico (14 dígitos + DV)."""
from __future__ import annotations

import re

_CNPJ_LEN = 14
_WEIGHTS_DV1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_WEIGHTS_DV2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def normalize_cnpj(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")


def _check_digit(base: str, weights: tuple[int, ...]) -> int:
    total = sum(int(d) * w for d, w in zip(base, weights, strict=True))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def validate_cnpj(digits: str) -> str:
    if not digits.isdigit():
        raise ValueError("cnpj must be digits only after normalize")
    if len(digits) != _CNPJ_LEN:
        raise ValueError("cnpj must have exactly 14 digits")
    if digits == digits[0] * _CNPJ_LEN:
        raise ValueError("invalid cnpj")

    dv1 = _check_digit(digits[:12], _WEIGHTS_DV1)
    dv2 = _check_digit(digits[:12] + str(dv1), _WEIGHTS_DV2)
    expected = f"{dv1}{dv2}"
    if digits[-2:] != expected:
        raise ValueError("invalid cnpj check digits")
    return digits
