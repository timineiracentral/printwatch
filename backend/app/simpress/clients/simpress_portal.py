"""Cliente async Playwright para portal Simpress (ACL, listagem, download ZIP)."""
from __future__ import annotations

import re
from typing import Any

from playwright.async_api import Browser, Page, Playwright, async_playwright

from app.simpress.config import simpress_settings

LOGIN_URL = "https://ux.simpress.com.br/ng/autenticacao/login"
FATURAMENTOS_URL = "https://ux.simpress.com.br/Faturamentos/Index"
DEFAULT_PAGE_SIZE = 25
NAV_TIMEOUT_MS = 60_000
LOGIN_TIMEOUT_MS = 30_000


class SimpressPortalError(Exception):
    """Erro de comunicação ou validação com o portal UX."""


class SimpressPortalClient:
    """Uma sessão Chromium por run — login UX, ACL e fetch same-origin."""

    def __init__(
        self,
        *,
        email: str | None = None,
        password: str | None = None,
    ) -> None:
        self._email = (email or simpress_settings.email).strip()
        self._password = (password or simpress_settings.password).strip()
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> SimpressPortalClient:
        await self.open()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def open(self) -> None:
        if not self._email or not self._password:
            raise SimpressPortalError("credenciais Simpress não configuradas")
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._page = await self._browser.new_page()
            await self._login()
        except Exception:
            await self.close()
            raise

    async def close(self) -> None:
        page, browser, pw = self._page, self._browser, self._playwright
        self._page = self._browser = self._playwright = None
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass
        if pw is not None:
            try:
                await pw.stop()
            except Exception:
                pass

    async def _login(self) -> None:
        page = self._require_page()
        await page.goto(LOGIN_URL, wait_until="networkidle", timeout=NAV_TIMEOUT_MS)
        await page.locator("#inputEmail input, input[type='text']").first.fill(self._email)
        await page.locator("#inputSenha input, input[type='password']").first.fill(
            self._password
        )
        await page.locator("button.btnLogin").click()
        await page.wait_for_url(
            re.compile(r"/ng/(?!autenticacao)"),
            timeout=LOGIN_TIMEOUT_MS,
        )
        await page.goto(
            FATURAMENTOS_URL,
            wait_until="domcontentloaded",
            timeout=NAV_TIMEOUT_MS,
        )
        await page.wait_for_timeout(1500)

    def _require_page(self) -> Page:
        if self._page is None:
            raise SimpressPortalError("portal não aberto — use open() ou async with")
        return self._page

    async def fetch_contracts(self) -> list[dict[str, Any]]:
        page = self._require_page()
        raw = await page.evaluate(
            """async () => {
              const resp = await fetch(
                '/Faturamentos/BuscarFiltrosContratos',
                { credentials: 'same-origin' }
              );
              if (!resp.ok) {
                throw new Error('BuscarFiltrosContratos HTTP ' + resp.status);
              }
              return resp.json();
            }"""
        )
        models = (raw or {}).get("model") or []
        seen: set[Any] = set()
        contracts: list[dict[str, Any]] = []
        for item in models:
            code = item.get("codigoContrato")
            if code is None or code in seen:
                continue
            seen.add(code)
            contracts.append({"codigoContrato": code})
        return contracts

    async def list_invoices(
        self,
        *,
        contract_codes: list[str],
        cnpj: str,
        page: int = 1,
        page_size: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        browser_page = self._require_page()
        size = page_size or DEFAULT_PAGE_SIZE
        cnpj_filter = re.sub(r"\D", "", cnpj or "") or None
        payload = await browser_page.evaluate(
            """async ({ contractCodes, cnpjFilter, pageNum, pageSize }) => {
              const resp = await fetch('/faturamentos/obterListagem', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'X-Via-JavaScript': 'true',
                },
                body: JSON.stringify({
                  faturamentoFiltroSelecionadoModel: {
                    codigosContrato: contractCodes,
                    cnpj: cnpjFilter || null,
                    mesesReferencia: undefined,
                    status: undefined,
                    numeroNota: null,
                  },
                  paginacao: { numeroPagina: pageNum, tamanhoPagina: pageSize },
                }),
              });
              if (!resp.ok) {
                throw new Error('obterListagem HTTP ' + resp.status);
              }
              return resp.json();
            }""",
            {
                "contractCodes": contract_codes,
                "cnpjFilter": cnpj_filter,
                "pageNum": page,
                "pageSize": size,
            },
        )
        model = (payload or {}).get("model") or {}
        rows = list(model.get("dados") or [])
        total = int(model.get("totalDeItens") or 0)
        return rows, total

    async def download_boleto_zip(
        self, contract_code: str | int, invoice_number: str
    ) -> bytes:
        page = self._require_page()
        result = await page.evaluate(
            """async ({ contractCode, invoiceNumber }) => {
              const resp = await fetch('/faturamentos/downloadDocumentos', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/octet-stream',
                  'X-Via-JavaScript': 'true',
                },
                body: JSON.stringify({
                  organizarZipPor: 0,
                  contratoNotas: [{
                    codigoContrato: contractCode,
                    listaNumeroNotas: [invoiceNumber],
                  }],
                  tipoDocumentoParaDownload: 1,
                }),
              });
              const ctype = resp.headers.get('content-type') || '';
              const buf = await resp.arrayBuffer();
              return {
                status: resp.status,
                ctype,
                bytes: Array.from(new Uint8Array(buf)),
              };
            }""",
            {"contractCode": contract_code, "invoiceNumber": invoice_number},
        )
        status = int(result.get("status") or 0)
        if status < 200 or status >= 300:
            raise SimpressPortalError(f"downloadDocumentos HTTP {status}")
        ctype = (result.get("ctype") or "").lower()
        if "zip" not in ctype and "octet-stream" not in ctype:
            raise SimpressPortalError(f"content-type inesperado: {ctype or 'vazio'}")
        raw = bytes(result.get("bytes") or [])
        if len(raw) < 2 or raw[:2] != b"PK":
            raise SimpressPortalError("resposta não é ZIP válido")
        return raw
