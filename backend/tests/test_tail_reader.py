from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.services.tail_reader import TailReader
from tests.conftest import CaptureState, StubStateRepo


def test_read_new_lines_empty_file(tmp_log_file, stub_state_repo: StubStateRepo) -> None:
    reader = TailReader(str(tmp_log_file), stub_state_repo)
    assert reader.read_new_lines() == []


def test_read_new_lines_returns_written_line(tmp_log_file, stub_state_repo: StubStateRepo) -> None:
    tmp_log_file.write_text("hello world\n", encoding="utf-8")
    reader = TailReader(str(tmp_log_file), stub_state_repo)
    assert reader.read_new_lines() == ["hello world"]


def test_read_new_lines_second_read_empty(tmp_log_file, stub_state_repo: StubStateRepo) -> None:
    tmp_log_file.write_text("line one\n", encoding="utf-8")
    reader = TailReader(str(tmp_log_file), stub_state_repo)
    assert reader.read_new_lines() == ["line one"]
    assert reader.read_new_lines() == []


def test_restart_same_inode_does_not_reread_old_lines(
    tmp_log_file, stub_state_repo: StubStateRepo
) -> None:
    tmp_log_file.write_text("old line\n", encoding="utf-8")
    reader1 = TailReader(str(tmp_log_file), stub_state_repo)
    assert reader1.read_new_lines() == ["old line"]
    reader1._fh.close()

    inode = os.stat(tmp_log_file).st_ino
    assert stub_state_repo.get() is not None
    assert stub_state_repo.get().inode == inode

    reader2 = TailReader(str(tmp_log_file), stub_state_repo)
    assert reader2.read_new_lines() == []

    with tmp_log_file.open("a", encoding="utf-8") as fh:
        fh.write("new line\n")
    assert reader2.read_new_lines() == ["new line"]


def test_logrotate_inode_change_reopens_from_start(
    tmp_log_file, stub_state_repo: StubStateRepo
) -> None:
    tmp_log_file.write_text("fresh after rotate\n", encoding="utf-8")
    real_inode = os.stat(tmp_log_file).st_ino
    stub_state_repo._state = CaptureState(inode=real_inode + 9999, byte_offset=99999)

    reader = TailReader(str(tmp_log_file), stub_state_repo)
    lines = reader.read_new_lines()
    assert lines == ["fresh after rotate"]
