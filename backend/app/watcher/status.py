"""Singleton de módulo para encapsular o InotifyObserver global.

Motivação (Plano 03-01 / RESEARCH §5.1): endpoints de health check
não devem importar `_observer` direto de `app.main` — isso cria
acoplamento circular e dificulta testes via `monkeypatch`.

Uso:
    from app.watcher import status as watcher_status

    # No lifespan startup, após observer.start():
    watcher_status.register_observer(_observer)

    # No endpoint /api/v1/health:
    alive = watcher_status.is_alive()

    # No lifespan shutdown:
    watcher_status.clear()
"""
from __future__ import annotations

from typing import Any

_obs: Any = None


def register_observer(obs: Any) -> None:
    """Armazena referência ao observer (Inotify, Polling, mock de teste)."""
    global _obs
    _obs = obs


def is_alive() -> bool:
    """True se há observer registrado e seu `is_alive()` retorna True."""
    return _obs is not None and bool(_obs.is_alive())


def clear() -> None:
    """Reseta o singleton — usado no shutdown e em testes."""
    global _obs
    _obs = None
