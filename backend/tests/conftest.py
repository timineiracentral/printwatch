from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass
class CaptureState:
    inode: int
    byte_offset: int


class StubStateRepo:
    def __init__(self, state: CaptureState | None = None) -> None:
        self._state = state

    def get(self) -> CaptureState | None:
        return self._state

    def upsert(self, *, inode: int, byte_offset: int) -> None:
        self._state = CaptureState(inode=inode, byte_offset=byte_offset)


@pytest.fixture
def sample_page_log_line() -> str:
    return (
        "test_printer DOMAIN\usuario 42 [26/May/2026:14:30:00 +0000] "
        "total 3 - 192.168.1.10 relatorio.pdf na_iso_a4_210x297mm one-sided"
    )


@pytest.fixture
def tmp_log_file(tmp_path: Path) -> Path:
    path = tmp_path / "page_log"
    path.write_text("", encoding="utf-8")
    return path


@pytest.fixture
def stub_state_repo() -> StubStateRepo:
    return StubStateRepo()
