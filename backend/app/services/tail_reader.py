from __future__ import annotations

import os
from typing import IO, Any, Protocol


class StateRepo(Protocol):
    def get(self) -> Any | None: ...

    def upsert(self, *, inode: int, byte_offset: int) -> None: ...


class TailReader:
    def __init__(self, path: str, state_repo: StateRepo) -> None:
        self.path = path
        self._state_repo = state_repo
        self._fh: IO[str] | None = None
        self._inode: int | None = None
        self._offset = 0
        self._recover_checkpoint()

    def _recover_checkpoint(self) -> None:
        state = self._state_repo.get()
        current_stat = os.stat(self.path)
        current_inode = current_stat.st_ino

        if state is not None and state.inode == current_inode:
            self._inode = current_inode
            self._offset = state.byte_offset
            self._fh = open(self.path, "r", encoding="utf-8", errors="replace")
            self._fh.seek(self._offset)
        else:
            self._inode = current_inode
            self._offset = 0
            self._fh = open(self.path, "r", encoding="utf-8", errors="replace")

    def read_new_lines(self) -> list[str]:
        if self._fh is None:
            return []

        current_inode = os.stat(self.path).st_ino
        if current_inode != self._inode:
            self._fh.close()
            self._inode = current_inode
            self._offset = 0
            self._fh = open(self.path, "r", encoding="utf-8", errors="replace")

        lines = self._fh.readlines()
        if lines:
            self._offset = self._fh.tell()
            self._state_repo.upsert(inode=self._inode, byte_offset=self._offset)

        return [line.rstrip("\n") for line in lines if line.strip()]
