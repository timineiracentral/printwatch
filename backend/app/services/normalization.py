"""Normalização de campos derivados do `page_log` do CUPS.

GAP-02-01 (Fase 3, D-22): o `PageLogFormat` configurado em
`cupsd.conf.template` envelopa a linha inteira em aspas duplas,
contaminando o campo `printer` capturado pelo regex (e também `sides`,
fora do escopo deste módulo). Esta função remove aspas extremas e
espaços de forma idempotente.

Idempotência (`normalize(normalize(x)) == normalize(x)`) é mandatória
para que o backfill possa ser rodado N vezes em segurança.

Exemplos:
    >>> normalize_printer_name('"test_printer')
    'test_printer'
    >>> normalize_printer_name('"test_printer"')
    'test_printer'
    >>> normalize_printer_name("'test_printer'")
    'test_printer'
    >>> normalize_printer_name('  test_printer  ')
    'test_printer'
    >>> normalize_printer_name(None) is None
    True
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
