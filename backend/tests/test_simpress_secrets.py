"""Wave 0 RED stubs — ISO-02 no secret fields in schemas/models/health."""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

_FORBIDDEN = re.compile(r"(password|api_key|token|secret)", re.I)
_ALLOWED_HEALTH_KEYS = frozenset({"status", "db_reachable", "detail"})
# ponytail: zip_token is opaque doc id, not a credential — allowlist avoids false positive
_ALLOWED_FIELD_NAMES = frozenset({"zip_token"})


def _iter_simpress_schema_model_modules():
    import app.simpress as simpress_pkg

    for mod_info in pkgutil.walk_packages(
        simpress_pkg.__path__, simpress_pkg.__name__ + "."
    ):
        if "schemas" in mod_info.name or "models" in mod_info.name:
            yield importlib.import_module(mod_info.name)


def _field_names_from_module(mod: Any) -> list[str]:
    names: list[str] = []
    for _, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and hasattr(obj, "model_fields"):
            names.extend(obj.model_fields.keys())
        elif inspect.isclass(obj) and hasattr(obj, "__table__"):
            names.extend(c.name for c in obj.__table__.columns)
    return names


def _secret_like_field_names(*classes: Any) -> list[str]:
    offenders: list[str] = []
    for cls in classes:
        label = f"{cls.__module__}.{cls.__name__}"
        if hasattr(cls, "model_fields"):
            field_names = cls.model_fields.keys()
        elif hasattr(cls, "__table__"):
            field_names = (c.name for c in cls.__table__.columns)
        else:
            continue
        for name in field_names:
            if name in _ALLOWED_FIELD_NAMES:
                continue
            if _FORBIDDEN.search(name):
                offenders.append(f"{label}.{name}")
    return offenders


def test_simpress_schemas_have_no_secret_field_names() -> None:
    offenders: list[str] = []
    for mod in _iter_simpress_schema_model_modules():
        for name in _field_names_from_module(mod):
            if name in _ALLOWED_FIELD_NAMES:
                continue
            if _FORBIDDEN.search(name):
                offenders.append(f"{mod.__name__}.{name}")
    assert offenders == [], f"secret-like fields found: {offenders}"


def test_audit_schema_and_model_have_no_secret_field_names() -> None:
    from app.simpress.db.models import MessageAudit
    from app.simpress.schemas.audit import MessageAuditRead

    offenders = _secret_like_field_names(MessageAudit, MessageAuditRead)
    assert offenders == [], f"audit secret-like fields: {offenders}"


def test_simpress_package_has_no_users_departments_fk_imports() -> None:
    """CNPJ-02 guard: simpress must not FK to core org tables."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1] / "app" / "simpress"
    assert root.is_dir(), "app.simpress package missing"
    text = "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*.py"))
    assert "ForeignKey" not in text or (
        "users" not in text and "departments" not in text
    ), "simpress must not reference users/departments ForeignKey"


def test_health_body_keys_are_slim_and_secret_free(simpress_client_on: TestClient) -> None:
    r = simpress_client_on.get("/api/v1/simpress/health")
    assert r.status_code == 200, r.text
    keys = set(r.json().keys())
    assert keys <= _ALLOWED_HEALTH_KEYS
    for key in keys:
        assert not _FORBIDDEN.search(key)


def test_audit_list_response_has_no_secrets(simpress_client_on: TestClient) -> None:
    """ISO-02 / D-17 — GET /audit summary must not echo credentials or message body."""
    r = simpress_client_on.get("/api/v1/simpress/audit")
    assert r.status_code == 200, r.text
    payload = json.dumps(r.json())
    assert "ZAP_API_KEY" not in payload
    assert "pytest-secret-password-value" not in payload
    assert not re.search(r"message_body|body_text", payload, re.I)
