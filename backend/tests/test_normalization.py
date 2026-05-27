"""Tests for normalize_printer_name (GAP-02-01).

RED gate: este módulo será importado ANTES de implementar
`app.services.normalization` (Task 3). Esperado: ImportError.
"""
from __future__ import annotations

import pytest

from app.core.normalize import normalize_org_code, normalize_printer_name


def test_normalize_strips_leading_double_quote() -> None:
    assert normalize_printer_name('"test_printer') == "test_printer"


def test_normalize_strips_paired_double_quotes() -> None:
    assert normalize_printer_name('"test_printer"') == "test_printer"


def test_normalize_strips_paired_single_quotes() -> None:
    assert normalize_printer_name("'test_printer'") == "test_printer"


def test_normalize_strips_whitespace() -> None:
    assert normalize_printer_name("  test_printer  ") == "test_printer"


def test_normalize_returns_none_for_none() -> None:
    assert normalize_printer_name(None) is None


def test_normalize_preserves_clean_input() -> None:
    assert normalize_printer_name("test_printer") == "test_printer"


@pytest.mark.parametrize(
    "raw",
    [
        '"test_printer',
        '"test_printer"',
        "'test_printer'",
        "  test_printer  ",
        "test_printer",
        '"  test_printer  "',
    ],
)
def test_normalize_idempotent(raw: str) -> None:
    once = normalize_printer_name(raw)
    twice = normalize_printer_name(once)
    assert once == twice


def test_normalize_org_code_uppercases() -> None:
    assert normalize_org_code("  fin  ") == "FIN"


def test_normalize_org_code_none() -> None:
    assert normalize_org_code(None) is None
    assert normalize_org_code("") is None
    assert normalize_org_code("   ") is None
