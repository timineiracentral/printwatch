"""Wave 0 RED stubs — ISO-02 no secret fields in schemas/models/health."""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

_FORBIDDEN = re.compile(r"(password|api_key|token|secret)", re.I)
_ALLOWED_HEALTH_KEYS = frozenset({"status", "db_reachable", "detail"})


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


def test_simpress_schemas_have_no_secret_field_names() -> None:
    offenders: list[str] = []
    for mod in _iter_simpress_schema_model_modules():
        for name in _field_names_from_module(mod):
            if _FORBIDDEN.search(name):
                offenders.append(f"{mod.__name__}.{name}")
    assert offenders == [], f"secret-like fields found: {offenders}"


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
