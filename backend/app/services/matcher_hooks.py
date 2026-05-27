"""Hooks para matcher on-save (D-03) — lazy import até plan 05-05."""


def schedule_match_for_queue(cups_queue_name: str) -> None:
    """Agenda match imediato para fila; no-op se matcher ainda não existir."""
    try:
        from app.services.printer_matcher import schedule_match_for_queue as _impl
    except ImportError:
        return
    _impl(cups_queue_name)
