"""Testes /api/v1/health e /healthz preservado (D-25)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok_when_watcher_alive(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "status": "ok",
        "db_reachable": True,
        "watcher_alive": True,
    }


def test_health_degraded_when_watcher_down(
    client: TestClient, monkeypatch
) -> None:
    from app.watcher import status as watcher_status

    monkeypatch.setattr(watcher_status, "is_alive", lambda: False)
    r = client.get("/api/v1/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "degraded"
    assert body["db_reachable"] is True
    assert body["watcher_alive"] is False


def test_health_503_when_db_unreachable(
    client: TestClient, monkeypatch
) -> None:
    from sqlalchemy.exc import OperationalError

    def _explode(*args, **kwargs):
        raise OperationalError("simulated", {}, BaseException("db down"))

    # Patch via método de instância — TestClient injeta a sessão via Depends.
    from sqlalchemy.orm import Session

    monkeypatch.setattr(Session, "execute", _explode)
    r = client.get("/api/v1/health")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "down"
    assert body["db_reachable"] is False


def test_healthz_continues_to_work(client: TestClient) -> None:
    """Endpoint legado da Fase 2 deve continuar respondendo."""
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "watcher" in body
