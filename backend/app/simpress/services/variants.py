"""Loader de variantes JSON versionadas por stage (D-09..D-11)."""
from __future__ import annotations

import json
import random
from pathlib import Path

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "reminders"
_VALID_STAGES = frozenset({"new", "reminded_5d", "reminded_10d", "overdue_urgent"})


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render(body: str, fields: dict[str, str]) -> str:
    return body.format_map(_SafeDict(fields))


def pick_variant(stage: str, fields: dict[str, str]) -> tuple[str, str]:
    """Retorna (variant_id, body renderizado) — não persiste body (D-17)."""
    if stage not in _VALID_STAGES:
        raise ValueError(f"stage desconhecido: {stage}")
    path = _TEMPLATES_DIR / f"{stage}.json"
    variants = json.loads(path.read_text(encoding="utf-8"))
    choice = random.choice(variants)
    return choice["id"], _render(choice["body"], fields)
