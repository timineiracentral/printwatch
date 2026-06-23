from __future__ import annotations


def classify_color_mode(
    raw_canonical: str | None,
    raw_source: str | None,
    printer_color_capability: str | None,
) -> tuple[str | None, str | None]:
    """Retorna (color_mode, color_mode_source) com precedência multi-fonte.

  Precedência: manual → captured → mono_only → pendente (None).
  Heurística baseada em nome de arquivo está reservada para fases futuras.
  """
    if raw_source == "manual":
        return raw_canonical, "manual"

    if raw_canonical is not None and raw_source == "captured":
        if printer_color_capability == "mono_only":
            return "mono", "mono_only"
        return raw_canonical, "captured"

    if printer_color_capability == "mono_only":
        return "mono", "mono_only"

    return None, None
