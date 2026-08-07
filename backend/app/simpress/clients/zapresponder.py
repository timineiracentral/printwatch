"""Cliente async httpx para ZapResponder (CAD-02, D-14)."""
from __future__ import annotations

from typing import Any

import httpx

from app.simpress.config import simpress_settings


class ZapNotConnected(Exception):
    """Sessão WhatsApp indisponível ou desconectada."""


class ZapSendError(Exception):
    """Falha HTTP ou resposta de erro do provider."""


class ZapResponderClient:
    """POST text/document via Bearer — sessão fixa em env (sem auto-pick)."""

    def __init__(self) -> None:
        api_key = simpress_settings.zap_api_key.strip()
        session_id = simpress_settings.zap_session_id.strip()
        if not api_key:
            raise RuntimeError("ZAP_API_KEY não configurada")
        if not session_id:
            raise RuntimeError("ZAP_SESSION_ID não configurada")
        self._session_id = session_id
        self._client = httpx.AsyncClient(
            base_url=simpress_settings.zap_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def __aenter__(self) -> ZapResponderClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def is_connected(self) -> bool:
        r = await self._client.get(f"/api/whatsapp/{self._session_id}")
        if r.status_code >= 400:
            return False
        sess = (r.json() or {}).get("sessao") or {}
        if not isinstance(sess, dict):
            return False
        return sess.get("status") == "CONECTADO" or bool(sess.get("isConected"))

    async def send_text(
        self,
        *,
        number: str,
        message: str,
        **extra: Any,
    ) -> dict[str, Any]:
        return await self._send(
            {
                "type": "text",
                "number": number,
                "message": message,
                "showInChat": True,
                **extra,
            }
        )

    async def send_document(
        self,
        *,
        number: str,
        url: str,
        file_name: str,
        **extra: Any,
    ) -> dict[str, Any]:
        return await self._send(
            {
                "type": "document",
                "number": number,
                "url": url,
                "file_name": file_name,
                **extra,
            }
        )

    async def _send(self, payload: dict[str, Any]) -> dict[str, Any]:
        r = await self._client.post(
            f"/api/whatsapp/message/{self._session_id}",
            json=payload,
        )
        data: dict[str, Any] = {}
        if r.content:
            try:
                parsed = r.json()
                if isinstance(parsed, dict):
                    data = parsed
            except ValueError:
                pass
        if r.status_code >= 400 or data.get("error") is True:
            raise ZapSendError(f"zap send failed: HTTP {r.status_code}")
        provider_id = None
        nested = data.get("response")
        if isinstance(nested, dict):
            inner = nested.get("response")
            if isinstance(inner, dict):
                provider_id = inner.get("id")
        return {
            "error": False,
            "status": r.status_code,
            "id": provider_id,
            "raw": data,
        }
