"""Cliente async Playwright para portal Simpress UX (SYNC-01)."""
from __future__ import annotations

import json
import re
from typing import Any

from app.simpress.config import simpress_settings

_INDEX_URL = "https://ux.simpress.com.br/Faturamentos/Index"
_LOGIN_URL = "https://ux.simpress.com.br/ng/autenticacao/login"
_STATUS_BY_CODE = {1: "Vencido", 2: "A Vencer", 3: "Pago", 4: "Cancelado"}


class SimpressPortalClient:
    """Uma sessão/browser por run — credenciais env-only (ISO-02)."""

    def __init__(self) -> None:
        self._playwright: Any = None
        self._browser: Any = None
        self._page: Any = None

    async def __aenter__(self) -> SimpressPortalClient:
        await self.open()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def open(self) -> None:
        from playwright.async_api import async_playwright

        email = simpress_settings.email.strip()
        password = simpress_settings.password.strip()
        if not email or not password:
            raise RuntimeError("credenciais Simpress não configuradas")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._page = await self._browser.new_page()
        page = self._page
        await page.goto(_LOGIN_URL, wait_until="networkidle", timeout=60000)
        await page.locator("#inputEmail input, input[type='text']").first.fill(email)
        await page.locator("#inputSenha input, input[type='password']").first.fill(
            password
        )
        await page.locator("button.btnLogin").click()
        await page.wait_for_url(re.compile(r"/ng/(?!autenticacao)"), timeout=30000)
        await page.goto(_INDEX_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1500)

    async def close(self) -> None:
        try:
            if self._browser is not None:
                await self._browser.close()
        finally:
            if self._playwright is not None:
                await self._playwright.stop()
        self._browser = None
        self._page = None
        self._playwright = None

    async def fetch_contracts(self) -> list[dict[str, Any]]:
        page = self._page
        if page is None:
            raise RuntimeError("portal não aberto")
        payload = await page.evaluate(
            """async () => {
              const resp = await fetch('/Faturamentos/BuscarFiltrosContratos', {credentials:'same-origin'});
              const data = await resp.json();
              return (data.model || []).map(c => ({ codigoContrato: c.codigoContrato }));
            }"""
        )
        return list(payload or [])

    async def list_invoices(
        self,
        *,
        contract_codes: list[str],
        cnpj: str,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[dict[str, Any]], int]:
        pg = self._page
        if pg is None:
            raise RuntimeError("portal não aberto")
        body = json.dumps(
            {
                "faturamentoFiltroSelecionadoModel": {
                    "codigosContrato": contract_codes,
                    "cnpj": cnpj,
                    "mesesReferencia": None,
                    "status": None,
                    "numeroNota": None,
                },
                "paginacao": {"numeroPagina": page, "tamanhoPagina": page_size},
            }
        )
        result = await pg.evaluate(
            """async (bodyJson) => {
              const resp = await fetch('/faturamentos/obterListagem', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'X-Via-JavaScript': 'true',
                },
                body: bodyJson,
              });
              const data = await resp.json();
              const model = data.model || {};
              const rows = model.dados || [];
              return { total: model.totalDeItens || 0, rows };
            }""",
            body,
        )
        rows = []
        for row in result.get("rows") or []:
            status_raw = row.get("statusPagamento")
            if isinstance(status_raw, int):
                status_raw = _STATUS_BY_CODE.get(status_raw, status_raw)
            rows.append(
                {
                    "cnpj": row.get("cnpj"),
                    "numeroNota": row.get("numeroNota"),
                    "valor": row.get("valor"),
                    "statusPagamento": status_raw,
                    "dataEmissao": row.get("dataEmissao"),
                    "dataVencimento": row.get("dataVencimento"),
                    "referencia": row.get("referencia"),
                    "contrato": {"codigoContrato": row.get("contrato", {}).get("codigoContrato")},
                }
            )
        return rows, int(result.get("total") or 0)

    async def download_zip(self, *, contract_code: str, invoice_number: str) -> bytes:
        pg = self._page
        if pg is None:
            raise RuntimeError("portal não aberto")
        body = json.dumps(
            {
                "organizarZipPor": 0,
                "contratoNotas": [
                    {
                        "codigoContrato": contract_code,
                        "listaNumeroNotas": [invoice_number],
                    }
                ],
                "tipoDocumentoParaDownload": 1,
            }
        )
        raw_list = await pg.evaluate(
            """async (bodyJson) => {
              const resp = await fetch('/faturamentos/downloadDocumentos', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/octet-stream',
                  'X-Via-JavaScript': 'true',
                },
                body: bodyJson,
              });
              if (!resp.ok) throw new Error('download falhou: ' + resp.status);
              const ctype = resp.headers.get('content-type') || '';
              if (!ctype.includes('zip') && !ctype.includes('octet-stream')) {
                throw new Error('content-type inválido: ' + ctype);
              }
              const buf = await resp.arrayBuffer();
              return Array.from(new Uint8Array(buf));
            }""",
            body,
        )
        data = bytes(raw_list)
        if len(data) < 2 or data[:2] != b"PK":
            raise ValueError("download não retornou ZIP")
        return data
