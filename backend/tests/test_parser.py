from datetime import datetime

import pytest

from app.services.parser import _null_if_dash, parse_page_log_line


def test_parse_page_log_line_sample_fields(sample_page_log_line: str) -> None:
    result = parse_page_log_line(sample_page_log_line)
    assert result is not None
    assert result["printer"] == "test_printer"
    assert result["username"] == "DOMAIN\\usuario"
    assert result["job_id"] == 42
    assert result["pages"] == 3
    assert result["color_mode"] is None
    assert result["host_origin"] == "192.0.2.1"
    assert result["job_name"] == "relatorio.pdf"
    assert result["media"] == "na_iso_a4_210x297mm"
    assert result["sides"] == "one-sided"


def test_null_if_dash_sentinel() -> None:
    assert _null_if_dash("-") is None


def test_null_if_dash_preserves_value() -> None:
    assert _null_if_dash("color") == "color"


def test_null_if_dash_strips_spaces() -> None:
    assert _null_if_dash("  -  ") is None


def test_parse_page_log_line_malformed_returns_none() -> None:
    assert parse_page_log_line("not a valid page log line at all") is None


def test_parse_page_log_line_empty_returns_none() -> None:
    assert parse_page_log_line("") is None


def test_parse_page_log_line_timestamp_timezone_aware(sample_page_log_line: str) -> None:
    result = parse_page_log_line(sample_page_log_line)
    assert result is not None
    ts = result["timestamp"]
    assert isinstance(ts, datetime)
    assert ts.tzinfo is not None


def test_parse_page_log_line_username_unchanged() -> None:
    # Valida que o parser preserva o formato DOMAIN\user exatamente como
    # recebido do CUPS, sem normalizar ou remover o prefixo de domínio (D-08).
    line = (
        "p DOMAIN\\user.example 1 [26/May/2026:14:30:00 +0000] "
        "total 1 - - doc.pdf media one-sided"
    )
    result = parse_page_log_line(line)
    assert result is not None
    assert result["username"] == "DOMAIN\\user.example"


def test_parse_page_log_line_status_allowed(sample_page_log_line: str) -> None:
    result = parse_page_log_line(sample_page_log_line)
    assert result is not None
    assert result["status"] == "allowed"


def test_parse_page_log_line_copies_none(sample_page_log_line: str) -> None:
    result = parse_page_log_line(sample_page_log_line)
    assert result is not None
    assert result["copies"] is None


def test_parser_strips_printer_quote_regression_gap_02_01() -> None:
    # Regressão GAP-02-01: PageLogFormat do CUPS pode envolver a linha
    # inteira em aspas duplas, fazendo o campo `printer` iniciar com `"`.
    # `normalize_printer_name` deve remover a aspa inicial (D-22).
    # Linha sintética que reproduz o padrão observado em produção.
    # IPs usam faixas TEST-NET RFC 5737 (192.0.2.x — nunca roteável).
    raw_line = (
        '"test_printer user.example 1 [26/May/2026:19:58:49 +0000] '
        'total 0 - 192.0.2.1 Test Page - -"'
    )
    parsed = parse_page_log_line(raw_line)
    assert parsed is not None, "Regex deve casar com linha no padrão GAP-02-01"
    assert parsed["printer"] == "test_printer", (
        f"GAP-02-01: printer deve ser limpo de aspas. Got: {parsed['printer']!r}"
    )
    assert not parsed["printer"].startswith('"'), "Não pode começar com aspa"
    assert not parsed["printer"].startswith("'"), "Não pode começar com apóstrofo"
    assert parsed["username"] == "user.example"
    assert parsed["job_id"] == 1
    assert parsed["pages"] == 0
    assert parsed["host_origin"] == "192.0.2.1"
    assert parsed["job_name"] == "Test Page"
    assert parsed["media"] is None  # `-` → null via _null_if_dash
