"""Testes /api/v1/export/csv (EXPORT-01..04, D-11..D-19)."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient


def _decode(body: bytes) -> str:
    # Cliente real Excel pt-BR lê como UTF-8 com BOM → strip BOM aqui
    # apenas para asserts; o ponto crítico é que o BOM ESTÁ presente.
    return body.decode("utf-8-sig")


def test_export_csv_returns_streaming_csv(client: TestClient, seed_jobs) -> None:
    r = client.get("/api/v1/export/csv")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "charset=utf-8" in r.headers["content-type"]


def test_export_csv_starts_with_bom_utf8(client: TestClient, seed_jobs) -> None:
    """D-12: BOM \\ufeff garante UTF-8 detectado pelo Excel pt-BR."""
    r = client.get("/api/v1/export/csv")
    assert r.content[:3] == b"\xef\xbb\xbf", r.content[:10]


def test_export_csv_uses_semicolon_delimiter(client: TestClient, seed_jobs) -> None:
    """D-13: separador `;` (locale pt-BR padrão Excel)."""
    text = _decode(r := client.get("/api/v1/export/csv").content)
    header = text.splitlines()[0]
    assert ";" in header
    assert "," not in header.split(";")[0]


def test_export_csv_header_pt_br(client: TestClient, seed_jobs) -> None:
    """D-14: cabeçalhos em pt-BR."""
    text = _decode(client.get("/api/v1/export/csv").content)
    header = text.splitlines()[0]
    expected = "Data/Hora;Usuário;Impressora;Documento;Páginas;Papel;Frente/Verso;Modo de Cor;Origem"
    assert header == expected


def test_export_csv_rows_match_jobs_endpoint(
    client: TestClient, seed_jobs
) -> None:
    """Linhas CSV == jobs agregados de `/api/v1/jobs` (D-11)."""
    text = _decode(client.get("/api/v1/export/csv").content)
    data_rows = text.splitlines()[1:]
    list_resp = client.get("/api/v1/jobs", params={"size": 500}).json()
    assert len(data_rows) == list_resp["total"], (
        f"CSV={len(data_rows)} jobs={list_resp['total']}"
    )


def test_export_csv_filename_in_content_disposition(
    client: TestClient, seed_jobs
) -> None:
    """D-17: filename `print_jobs_YYYYMMDD_HHMM.csv`."""
    r = client.get("/api/v1/export/csv")
    cd = r.headers["content-disposition"]
    assert "attachment" in cd
    assert "filename=" in cd
    assert ".csv" in cd
    assert "print_jobs_" in cd


def test_export_csv_x_total_rows_header(client: TestClient, seed_jobs) -> None:
    r = client.get("/api/v1/export/csv")
    list_resp = client.get("/api/v1/jobs", params={"size": 1}).json()
    assert r.headers["x-total-rows"] == str(list_resp["total"])


def test_export_csv_escapes_special_chars(
    client: TestClient, db_session
) -> None:
    """RFC 4180: aspas/`;`/newline são envolvidos e aspas duplicadas."""
    from app.db.models import PrintJob

    db_session.add(
        PrintJob(
            printer="alpha",
            username="usr",
            job_id=999,
            job_name='Arq;com "aspas"\nlinha',
            timestamp=datetime(2026, 5, 26, 12, 0, 0),
            pages=1,
            host_origin="h",
        )
    )
    db_session.commit()

    text = _decode(client.get("/api/v1/export/csv").content)
    # Documento agora envolto em aspas e aspas internas duplicadas
    assert '"Arq;com ""aspas""' in text, text


def test_export_csv_filter_username(client: TestClient, seed_jobs) -> None:
    text = _decode(
        client.get("/api/v1/export/csv", params={"username": "usr1"}).content
    )
    rows = text.splitlines()[1:]
    assert len(rows) == 1
    assert "usr1" in rows[0]


def test_export_csv_cap_100k_returns_400(client: TestClient, seed_jobs) -> None:
    """D-16: cap defensivo no service."""
    with patch("app.api.v1.export.csv_export.count_aggregated", return_value=100_001):
        r = client.get("/api/v1/export/csv")
    assert r.status_code == 400
    body = r.json()
    assert "100" in body["detail"]
    assert "linhas" in body["detail"]


def test_export_csv_uses_streaming_response(client: TestClient, seed_jobs) -> None:
    """StreamingResponse → conteúdo não materializado em memória.

    Validação indireta: o body é construído por generator, então o
    Content-Length pode estar ausente e o transfer-encoding pode ser
    chunked. Em TestClient, basta confirmar que a response é iterada.
    """
    from fastapi.responses import StreamingResponse
    from app.api.v1 import export as export_mod

    original_make = export_mod.export_csv_endpoint
    captured: dict = {}

    def _wrap(*args, **kwargs):
        resp = original_make(*args, **kwargs)
        captured["resp"] = resp
        return resp

    # Patch direto: chama a função de produção e confere o tipo.
    from app.db.session import get_db_dep
    from app.schemas.jobs import JobFilters

    db = next(get_db_dep())
    try:
        resp = export_mod.export_csv_endpoint(filters=JobFilters(), db=db)
        assert isinstance(resp, StreamingResponse), type(resp)
    finally:
        db.close()


def test_export_csv_in_openapi(client: TestClient) -> None:
    paths = client.get("/api/v1/openapi.json").json()["paths"]
    assert "/api/v1/export/csv" in paths


def test_export_csv_timestamp_in_local_tz(
    client: TestClient, db_session
) -> None:
    """UTC no banco → America/Sao_Paulo na coluna `Data/Hora` (D-18)."""
    from app.db.models import PrintJob

    # 18:00 UTC = 15:00 SP (BRT -03:00).
    db_session.add(
        PrintJob(
            printer="p", username="u", job_id=1,
            job_name="job", timestamp=datetime(2026, 5, 26, 18, 0, 0),
            pages=1, host_origin="h",
        )
    )
    db_session.commit()
    text = _decode(client.get("/api/v1/export/csv").content)
    # 18:00 UTC -3h = 15:00 SP
    assert "2026-05-26 15:00:00" in text, text
