#!/usr/bin/env python3
"""Atualiza credenciais Simpress/Zap no .env da VM via SSH (não imprime segredos)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("SIMPRESS_EMAIL", "SIMPRESS_PASSWORD", "ZAP_API_KEY")
SSH_HOST = "paperclip-vm"
REMOTE_DIR = "~/printwatch"


def _parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    local = _parse_env(ROOT / ".env")
    missing = [k for k in KEYS if not local.get(k)]
    if missing:
        raise SystemExit(f"Faltam no .env local: {', '.join(missing)}")

    lines = ["import pathlib", "updates = {"]
    for k in KEYS:
        v = local[k].replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"    '{k}': '{v}',")
    lines.extend(
        [
            "}",
            "p = pathlib.Path('.env')",
            "raw = p.read_text(encoding='utf-8').splitlines() if p.exists() else []",
            "out, seen = [], set()",
            "for line in raw:",
            "    if not line.strip() or line.lstrip().startswith('#') or '=' not in line:",
            "        out.append(line)",
            "        continue",
            "    key = line.split('=', 1)[0].strip()",
            "    if key in updates:",
            "        out.append(f'{key}={updates[key]}')",
            "        seen.add(key)",
            "    else:",
            "        out.append(line)",
            "for key, val in updates.items():",
            "    if key not in seen:",
            "        out.append(f'{key}={val}')",
            "p.write_text('\\n'.join(out) + '\\n', encoding='utf-8')",
            "print('ok', ','.join(sorted(updates)))",
        ]
    )
    remote_py = "\n".join(lines)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(remote_py)
        tmp = f.name

    try:
        subprocess.run(["scp", tmp, f"{SSH_HOST}:/tmp/pw_env_update.py"], check=True)
        r = subprocess.run(
            ["ssh", SSH_HOST, f"cd {REMOTE_DIR} && python3 /tmp/pw_env_update.py && rm /tmp/pw_env_update.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(r.stdout.strip())
    finally:
        Path(tmp).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
