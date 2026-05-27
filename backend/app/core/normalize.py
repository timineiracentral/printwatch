"""Normalização compartilhada (D-05, D-30).

Módulo sem dependência de SQLAlchemy — importável pelo watcher, parser,
matcher e API sem acoplar ao pacote services.
"""
from __future__ import annotations

from typing import Optional


def normalize_printer_name(raw: Optional[str]) -> Optional[str]:
    """Idempotent strip de aspas extremas (`"` e `'`) + whitespace.

    Cobre tanto o caso de aspas pareadas (a linha CUPS é envelopada
    em `"..."`) quanto o caso degenerado de aspa solta no início
    (regex captura `\\S+` capturando o `"`).
    """
    if raw is None:
        return None
    s = raw.strip()
    while len(s) >= 2 and s[0] in ('"', "'") and s[0] == s[-1]:
        s = s[1:-1].strip()
    s = s.lstrip('"').lstrip("'").rstrip('"').rstrip("'").strip()
    return s


def normalize_org_code(raw: Optional[str]) -> Optional[str]:
    """Strip, uppercase; None se vazio após normalização (D-16)."""
    if raw is None:
        return None
    s = raw.strip().upper()
    return s if s else None
