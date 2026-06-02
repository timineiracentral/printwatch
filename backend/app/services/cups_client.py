"""Cliente CUPS async para consulta de status de fila (FLEET-01)."""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_ONLINE_MARKERS = ("idle", "printing", "processing")
_OFFLINE_MARKERS = ("disabled", "stopped")


async def get_queue_state(queue_name: str) -> tuple[bool, str | None]:
    """Executa lpstat -p {queue} com timeout 5s.

    Returns:
        (success, reason) — success True quando lpstat parseável;
        reason None em sucesso parseado, ou mensagem de erro.
    """
    cmd = ["lpstat", "-p", queue_name]
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=5.0,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=5.0)
    except asyncio.TimeoutError:
        return False, "lpstat timeout"
    except FileNotFoundError:
        return False, "lpstat not found"
    except OSError as exc:
        return False, str(exc)

    stdout = stdout_bytes.decode(errors="replace").lower()
    stderr = stderr_bytes.decode(errors="replace").strip()

    if proc.returncode != 0:
        reason = stderr or f"lpstat exit {proc.returncode}"
        return False, reason

    if any(marker in stdout for marker in _OFFLINE_MARKERS):
        return True, "offline"

    if any(marker in stdout for marker in _ONLINE_MARKERS):
        return True, "online"

    return False, "unrecognized lpstat output"


def parse_queue_state(stdout: str) -> str | None:
    """Parse lpstat stdout → 'online' | 'offline' | None."""
    text = stdout.lower()
    if any(marker in text for marker in _OFFLINE_MARKERS):
        return "offline"
    if any(marker in text for marker in _ONLINE_MARKERS):
        return "online"
    return None
