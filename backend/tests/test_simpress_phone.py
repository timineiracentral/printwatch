"""Wave 0 RED stubs — phone normalize/validate (D-16..D-19)."""
from __future__ import annotations

import pytest

from app.simpress.phone import normalize_phone, validate_phone


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("+55 31 99999-9999", "5531999999999"),
    ],
)
def test_normalize_phone_strips_non_digits(raw: str, expected: str) -> None:
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize(
    "digits",
    [
        "",
        "abc",
        "123456789",
        "1" * 16,
        "0319999999999",
    ],
)
def test_validate_phone_rejects_invalid(digits: str) -> None:
    with pytest.raises(ValueError):
        validate_phone(digits)


def test_validate_phone_rejects_letters_after_normalize_path() -> None:
    normalized = normalize_phone("abc-only")
    with pytest.raises(ValueError):
        validate_phone(normalized)


def test_validate_phone_accepts_valid_brazil_mobile() -> None:
    assert validate_phone("5531999999999") == "5531999999999"
