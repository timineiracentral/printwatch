"""Wave 2 RED — SYNC-01/02, D-03..D-09, D-05, D-12 via sync_service."""
from __future__ import annotations

import asyncio
import importlib
import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select

from tests.conftest_simpress import DEFAULT_ZIP_BYTES, FakePortal, portal_row

_VALID_CNPJ = "11222333000181"
_OTHER_CNPJ = "11444777000161"


def _sync_service():
    try:
        return importlib.import_module("app.simpress.services.sync_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"sync_service não implementado: {exc}")


def _invoices_service():
    try:
        return importlib.import_module("app.simpress.services.invoices_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"invoices_service não implementado: {exc}")


def _seed_cnpj(db: Any, *, cnpj: str = _VALID_CNPJ, name: str = "Empresa Teste") -> Any:
    from app.simpress.schemas.cnpj import CnpjCreate
    from app.simpress.services import cnpjs_service

    return cnpjs_service.create_cnpj(db, CnpjCreate(cnpj=cnpj, name=name))


def _summary_list(summary: Any, attr: str, json_attr: str) -> list[Any]:
    value = getattr(summary, attr, None)
    if value is not None:
        return list(value)
    raw = getattr(summary, json_attr, None)
    return json.loads(raw or "[]")


def _run_sync(db: Any, portal: FakePortal) -> Any:
    sync_service = _sync_service()
    return asyncio.run(
        sync_service.run_sync(db, portal_factory=lambda: portal)
    )


def _open_invoices(db: Any) -> list[Any]:
    invoices_service = _invoices_service()
    return invoices_service.list_open_invoices(db)


def _invoice_by_nota(db: Any, nota: str) -> Any | None:
    from app.simpress.db.models import Invoice

    return db.scalars(
        select(Invoice).where(Invoice.invoice_number == nota)
    ).first()


def test_acl_contracts_called_before_listing(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [portal_row()]
    _run_sync(simpress_session, fake_portal)

    assert fake_portal.contracts_called >= 1
    assert fake_portal.list_calls, "listagem deve ocorrer após ACL"
    assert fake_portal.contracts_called == 1


def test_sem_cnpjs_ativos_nao_abre_portal(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    summary = _run_sync(simpress_session, fake_portal)

    assert fake_portal.contracts_called == 0
    assert fake_portal.list_calls == []
    assert summary.ok is True
    assert summary.contracts_count == 0


def test_listagem_ignora_rows_de_outro_cnpj(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(cnpj=_VALID_CNPJ, numero_nota="NF-OK"),
        portal_row(cnpj=_OTHER_CNPJ, numero_nota="NF-SKIP"),
    ]
    _run_sync(simpress_session, fake_portal)

    open_notas = {row.invoice_number for row in _open_invoices(simpress_session)}
    assert open_notas == {"NF-OK"}


def test_listagem_filtra_por_cnpjs_ativos(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    active = _seed_cnpj(simpress_session, cnpj=_VALID_CNPJ, name="Ativo")
    inactive = _seed_cnpj(simpress_session, cnpj=_OTHER_CNPJ, name="Inativo")
    from app.simpress.services import cnpjs_service

    cnpjs_service.soft_delete_cnpj(simpress_session, inactive.id)

    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [portal_row(cnpj=_VALID_CNPJ)]
    fake_portal.rows_by_cnpj[_OTHER_CNPJ] = [
        portal_row(cnpj=_OTHER_CNPJ, numero_nota="NF-OTHER")
    ]
    _run_sync(simpress_session, fake_portal)

    listed_cnpjs = {call["cnpj"] for call in fake_portal.list_calls}
    assert listed_cnpjs == {active.cnpj}


def test_paginacao_percorre_todas_as_paginas(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.page_size = 2
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota=f"NF-{i:03d}") for i in range(5)
    ]
    _run_sync(simpress_session, fake_portal)

    pages = sorted({call["page"] for call in fake_portal.list_calls})
    assert pages == [1, 2, 3]


def test_d03_somente_vencido_a_vencer_entram_no_upsert(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-OPEN", status="Vencido"),
        portal_row(numero_nota="NF-SOON", status="A Vencer"),
        portal_row(numero_nota="NF-PAID", status="Pago"),
        portal_row(numero_nota="NF-CANC", status="Cancelado"),
    ]
    _run_sync(simpress_session, fake_portal)

    open_rows = _open_invoices(simpress_session)
    notas = {row.invoice_number for row in open_rows}
    assert notas == {"NF-OPEN", "NF-SOON"}
    assert _invoice_by_nota(simpress_session, "NF-PAID") is None
    assert _invoice_by_nota(simpress_session, "NF-CANC") is None


def test_atualiza_campos_e_status_de_fatura_existente(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-001", status="A Vencer", valor=100.0)
    ]
    _run_sync(simpress_session, fake_portal)

    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(
            numero_nota="NF-001",
            status="Vencido",
            valor=250.5,
            referencia="08/2026",
        )
    ]
    _run_sync(simpress_session, fake_portal)

    row = _invoice_by_nota(simpress_session, "NF-001")
    assert row is not None
    assert row.status == "Vencido"
    assert row.amount == Decimal("250.50")
    assert row.reference == "08/2026"


def test_d05_zero_rows_ativa_warning_sem_falhar_run(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    cnpj = _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = []
    summary = _run_sync(simpress_session, fake_portal)

    simpress_session.refresh(cnpj)
    assert cnpj.invoice_match_warning is True
    assert summary.ok is True
    warnings = _summary_list(summary, "cnpj_warnings", "cnpj_warnings_json")
    assert _VALID_CNPJ in warnings or any(_VALID_CNPJ in str(w) for w in warnings)


def test_d05_match_posterior_limpa_warning(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    cnpj = _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = []
    _run_sync(simpress_session, fake_portal)
    simpress_session.refresh(cnpj)
    assert cnpj.invoice_match_warning is True

    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [portal_row()]
    _run_sync(simpress_session, fake_portal)
    simpress_session.refresh(cnpj)
    assert cnpj.invoice_match_warning is False


def test_d06_d08_fechada_existente_purga_zip_e_some_da_lista_aberta(
    simpress_session: Any, fake_portal: FakePortal, simpress_docs_path: Path
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-CLOSE", status="Vencido")
    ]
    _run_sync(simpress_session, fake_portal)

    row = _invoice_by_nota(simpress_session, "NF-CLOSE")
    assert row is not None
    assert row.zip_token is not None
    zip_path = simpress_docs_path / f"{row.zip_token}.zip"
    assert zip_path.is_file()

    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-CLOSE", status="Pago")
    ]
    _run_sync(simpress_session, fake_portal)

    simpress_session.refresh(row)
    assert row.zip_token is None
    assert not zip_path.exists()
    open_notas = {inv.invoice_number for inv in _open_invoices(simpress_session)}
    assert "NF-CLOSE" not in open_notas
    assert row.status == "Pago"


def test_d03_fechada_nova_nao_cria_row(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-NEW-PAID", status="Pago"),
        portal_row(numero_nota="NF-NEW-CANC", status="Cancelado"),
    ]
    _run_sync(simpress_session, fake_portal)

    assert _invoice_by_nota(simpress_session, "NF-NEW-PAID") is None
    assert _invoice_by_nota(simpress_session, "NF-NEW-CANC") is None


def test_d04_zip_baixa_somente_quando_ausente(
    simpress_session: Any, fake_portal: FakePortal
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-ZIP", status="Vencido")
    ]
    _run_sync(simpress_session, fake_portal)
    first_downloads = len(fake_portal.download_calls)

    _run_sync(simpress_session, fake_portal)
    assert len(fake_portal.download_calls) == first_downloads


def test_d09_reabertura_sem_zip_baixa_novamente(
    simpress_session: Any, fake_portal: FakePortal, simpress_docs_path: Path
) -> None:
    _seed_cnpj(simpress_session)
    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-REOPEN", status="Vencido")
    ]
    _run_sync(simpress_session, fake_portal)
    downloads_after_open = len(fake_portal.download_calls)

    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-REOPEN", status="Pago")
    ]
    _run_sync(simpress_session, fake_portal)

    fake_portal.rows_by_cnpj[_VALID_CNPJ] = [
        portal_row(numero_nota="NF-REOPEN", status="Vencido")
    ]
    _run_sync(simpress_session, fake_portal)

    assert len(fake_portal.download_calls) == downloads_after_open + 1
    row = _invoice_by_nota(simpress_session, "NF-REOPEN")
    assert row is not None
    assert row.zip_token is not None
    assert (simpress_docs_path / f"{row.zip_token}.zip").is_file()


def test_erro_sanitizado_limita_cinco_e_finaliza_resumo(
    simpress_session: Any,
    simpress_sync_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_cnpj(simpress_session)

    class ExplodingPortal(FakePortal):
        async def fetch_contracts(self) -> list[dict[str, Any]]:
            raise RuntimeError(
                f"portal falhou email={os.environ['SIMPRESS_EMAIL']} "
                f"pass={os.environ['SIMPRESS_PASSWORD']}"
            )

    portal = ExplodingPortal()
    summary = _run_sync(simpress_session, portal)

    assert summary.finished_at is not None
    errors = _summary_list(summary, "errors", "errors_json")
    assert len(errors) <= 5
    blob = json.dumps(errors, ensure_ascii=False)
    assert os.environ["SIMPRESS_EMAIL"] not in blob
    assert os.environ["SIMPRESS_PASSWORD"] not in blob
