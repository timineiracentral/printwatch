from __future__ import annotations

import pytest

from app.services.color_mode import normalize_color_mode
from app.services.parser import parse_page_log_line


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("grayscale", "mono"),
        ("gray", "mono"),
        ("monochrome", "mono"),
        ("color", "color"),
        ("rgb", "color"),
        ("cmyk", "color"),
        (None, None),
        ("-", None),
        ("unknown-value", None),
        ("auto-monochrome", "mono"),
        ("process-monochrome", "mono"),
        ("bi-level", "mono"),
        ("color-monochrome", "mono"),
        ("auto", None),
    ],
)
def test_normalize_color_mode_aliases(raw: str | None, expected: str | None) -> None:
    canonical, _ = normalize_color_mode(raw)
    assert canonical == expected


def test_normalize_color_mode_grayscale_returns_mono_tuple() -> None:
    canonical, hint = normalize_color_mode("grayscale")
    assert canonical == "mono"
    assert hint == "captured"


def test_parse_page_log_line_sets_captured_source_for_known_color() -> None:
    line = (
        "test_printer user 1 [26/May/2026:14:30:00 +0000] "
        "total 1 color 192.0.2.1 doc.pdf media one-sided"
    )
    result = parse_page_log_line(line)
    assert result is not None
    assert result["color_mode"] == "color"
    assert result["color_mode_source"] == "captured"


def test_parse_page_log_line_pending_color_leaves_source_null() -> None:
    line = (
        "test_printer user 1 [26/May/2026:14:30:00 +0000] "
        "total 1 - 192.0.2.1 doc.pdf media one-sided"
    )
    result = parse_page_log_line(line)
    assert result is not None
    assert result["color_mode"] is None
    assert result["color_mode_source"] is None


def test_parse_page_log_line_unknown_color_not_dropped() -> None:
    line = (
        "test_printer user 1 [26/May/2026:14:30:00 +0000] "
        "total 1 exotic 192.0.2.1 doc.pdf media one-sided"
    )
    result = parse_page_log_line(line)
    assert result is not None
    assert result["color_mode"] is None
    assert result["color_mode_source"] is None
