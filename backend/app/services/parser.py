from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from app.core.normalize import normalize_printer_name

PAGE_LOG_REGEX = re.compile(
    r"^(\S+)\s+(\S+)\s+(\d+)\s+\[(.+?)\]\s+total\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)\s+(\S+)$"
)


def _null_if_dash(value: str) -> Optional[str]:
    """D-09: valor sentinel '-' do CUPS → NULL no banco."""
    return None if value.strip() == "-" else value.strip()


def parse_page_log_line(line: str) -> Optional[dict[str, Any]]:
    m = PAGE_LOG_REGEX.match(line.strip())
    if m is None:
        return None
    return {
        "printer": normalize_printer_name(m.group(1)),
        "username": m.group(2),
        "job_id": int(m.group(3)),
        "timestamp": datetime.strptime(m.group(4), "%d/%b/%Y:%H:%M:%S %z"),
        "pages": int(m.group(5)),
        "color_mode": _null_if_dash(m.group(6)),
        "host_origin": _null_if_dash(m.group(7)),
        "job_name": _null_if_dash(m.group(8)),
        "media": _null_if_dash(m.group(9)),
        "sides": _null_if_dash(m.group(10)),
        "copies": None,
        "status": "allowed",
    }
