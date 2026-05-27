from __future__ import annotations

_MONO_ALIASES = frozenset(
    {
        "grayscale",
        "gray",
        "grey",
        "monochrome",
        "bw",
        "black",
        "black-and-white",
        "1",
        "mono",
    }
)

_COLOR_ALIASES = frozenset(
    {
        "color",
        "colour",
        "rgb",
        "cmyk",
        "2",
    }
)


def normalize_color_mode(
    raw: str | None,
) -> tuple[str | None, str | None]:
    """Map CUPS page_log color field to canonical mono|color or pending (NULL).

    Returns (canonical, source_hint). source_hint is informational only;
    parser sets color_mode_source='captured' when canonical is not None.
    """
    if raw is None:
        return None, None

    key = raw.strip().lower()
    if not key or key == "-":
        return None, None

    if key in _MONO_ALIASES:
        return "mono", "captured"
    if key in _COLOR_ALIASES:
        return "color", "captured"

    return None, None
