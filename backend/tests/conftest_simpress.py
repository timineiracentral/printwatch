"""Fixtures Simpress — env antes do import/reload do app (ISO-01)."""
from __future__ import annotations

import asyncio
import importlib
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

DEFAULT_ZIP_BYTES = b"PK\x03\x04simpress-pytest-zip-payload"
PUBLIC_BASE_URL_TEST = "https://public.example.test"


def _reload_app():
    """Recarrega app.main após mudança de env (D-05/D-08)."""
    for mod in list(sys.modules):
        if mod.startswith("app.simpress"):
            del sys.modules[mod]
    import app.main as main_mod

    importlib.reload(main_mod)
    return main_mod


def _build_client(
    enabled: bool,
    db_path: str,
    *,
    docs_path: str | None = None,
    public_base_url: str = PUBLIC_BASE_URL_TEST,
) -> TestClient:
    os.environ["SIMPRESS_ENABLED"] = "true" if enabled else "false"
    os.environ["SIMPRESS_DB_PATH"] = db_path
    os.environ["PUBLIC_BASE_URL"] = public_base_url
    if docs_path is not None:
        os.environ["SIMPRESS_DOCS_PATH"] = docs_path
    main_mod = _reload_app()
    return TestClient(main_mod.app, raise_server_exceptions=False)


def portal_row(
    *,
    cnpj: str = "11222333000181",
    numero_nota: str = "NF-001",
    status: str = "Vencido",
    contract: str = "CTR001",
    valor: float = 150.0,
    referencia: str = "07/2026",
    data_emissao: str = "2026-07-01T00:00:00",
    data_vencimento: str = "2026-08-15T00:00:00",
) -> dict[str, Any]:
    """Shape validado no spike 001 — sem credenciais reais."""
    return {
        "cnpj": cnpj,
        "numeroNota": numero_nota,
        "valor": valor,
        "statusPagamento": status,
        "dataEmissao": data_emissao,
        "dataVencimento": data_vencimento,
        "referencia": referencia,
        "contrato": {"codigoContrato": contract},
    }


class FakePortal:
    """Portal determinístico — sem Playwright/rede/credenciais."""

    def __init__(
        self,
        *,
        contracts: list[dict[str, Any]] | None = None,
        rows_by_cnpj: dict[str, list[dict[str, Any]]] | None = None,
        zip_bytes: bytes | None = None,
        page_size: int = 25,
    ) -> None:
        self.contracts = contracts or [{"codigoContrato": "CTR001"}]
        self.rows_by_cnpj = rows_by_cnpj or {}
        self.zip_bytes = zip_bytes if zip_bytes is not None else DEFAULT_ZIP_BYTES
        self.page_size = page_size
        self.contracts_called = 0
        self.list_calls: list[dict[str, Any]] = []
        self.download_calls: list[dict[str, Any]] = []
        self._list_gate = asyncio.Event()
        self._list_gate.set()

    def block_listing(self) -> None:
        self._list_gate.clear()

    def unblock_listing(self) -> None:
        self._list_gate.set()

    async def fetch_contracts(self) -> list[dict[str, Any]]:
        self.contracts_called += 1
        return self.contracts

    async def list_invoices(
        self,
        *,
        contract_codes: list[str],
        cnpj: str,
        page: int = 1,
        page_size: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        await self._list_gate.wait()
        size = page_size or self.page_size
        self.list_calls.append(
            {
                "contract_codes": list(contract_codes),
                "cnpj": cnpj,
                "page": page,
                "page_size": size,
            }
        )
        rows = self.rows_by_cnpj.get(cnpj, [])
        start = (page - 1) * size
        return rows[start : start + size], len(rows)

    async def download_zip(self, *, contract_code: str, invoice_number: str) -> bytes:
        self.download_calls.append(
            {
                "contract_code": contract_code,
                "invoice_number": invoice_number,
            }
        )
        return self.zip_bytes

    async def close(self) -> None:
        return None


@pytest.fixture
def simpress_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "simpress-pytest.db")


@pytest.fixture
def simpress_docs_path(tmp_path: Path) -> Path:
    path = tmp_path / "simpress_docs"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def simpress_client_on(
    simpress_db_path: str, simpress_docs_path: Path
) -> Iterator[TestClient]:
    yield _build_client(True, simpress_db_path, docs_path=str(simpress_docs_path))


@pytest.fixture
def simpress_client_off(simpress_db_path: str, simpress_docs_path: Path) -> Iterator[TestClient]:
    yield _build_client(False, simpress_db_path, docs_path=str(simpress_docs_path))


@pytest.fixture
def fake_portal() -> FakePortal:
    return FakePortal()


@pytest.fixture
def simpress_session(simpress_client_on: TestClient) -> Iterator[Any]:
    """Session SQLAlchemy Simpress — schema já criado pelo client fixture."""
    from app.simpress.db.session import SimpressSessionLocal

    db = SimpressSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def simpress_sync_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Credenciais fake para asserts negativos nos resumos de erro."""
    monkeypatch.setenv("SIMPRESS_EMAIL", "sync-test@example.test")
    monkeypatch.setenv("SIMPRESS_PASSWORD", "pytest-secret-password-value")


def core_sqlite_path() -> str:
    return os.environ.get("DB_PATH", "")


def core_table_count(table: str) -> int:
    """Conta linhas em tabela do printwatch.db (core)."""
    path = core_sqlite_path()
    if not path or not os.path.exists(path):
        return 0
    conn = sqlite3.connect(path)
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


@pytest.fixture
def count_core_rows():
    """Fixture wrapper — conftest modules não são importáveis nos testes."""
    return core_table_count
