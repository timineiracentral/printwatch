from __future__ import annotations

import pytest

from app.services.color_classifier import classify_color_mode


@pytest.mark.parametrize(
    ("raw_canonical", "raw_source", "capability", "expected_mode", "expected_src"),
    [
        ("mono", "captured", None, "mono", "captured"),
        ("color", "captured", None, "color", "captured"),
        ("color", "captured", "mono_only", "mono", "mono_only"),
        ("mono", "captured", "mono_only", "mono", "mono_only"),
        (None, None, "mono_only", "mono", "mono_only"),
        (None, None, None, None, None),
        ("mono", "captured", "color", "mono", "captured"),
    ],
)
def test_classify_color_mode(
    raw_canonical: str | None,
    raw_source: str | None,
    capability: str | None,
    expected_mode: str | None,
    expected_src: str | None,
) -> None:
    mode, src = classify_color_mode(raw_canonical, raw_source, capability)
    assert mode == expected_mode
    assert src == expected_src
