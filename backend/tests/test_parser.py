from datetime import datetime

import pytest

from app.services.parser import _null_if_dash, parse_page_log_line


def test_parse_page_log_line_sample_fields(sample_page_log_line: str) -> None:
    result = parse_page_log_line(sample_page_log_line)
    assert result is not None
    assert result["printer"] == "test_printer"
    assert result["username"] == "DOMAIN\usuario"
    assert result["job_id"] == 42
    assert result["pages"] == 3
    assert result["color_mode"] is None
    assert result["host_origin"] == "192.168.1.10"
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
    line = (
        "p DOMAIN\user.example 1 [26/May/2026:14:30:00 +0000] "
        "total 1 - - doc.pdf media one-sided"
    )
    result = parse_page_log_line(line)
    assert result is not None
    assert result["username"] == "DOMAIN\user.example"


def test_parse_page_log_line_status_allowed(sample_page_log_line: str) -> None:
    result = parse_page_log_line(sample_page_log_line)
    assert result is not None
    assert result["status"] == "allowed"


def test_parse_page_log_line_copies_none(sample_page_log_line: str) -> None:
    result = parse_page_log_line(sample_page_log_line)
    assert result is not None
    assert result["copies"] is None
