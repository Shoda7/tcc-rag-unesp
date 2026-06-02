"""Scraper com suporte a JavaScript (Playwright).

Navega pelo portal fc.unesp.br (SPA xajax) usando Chrome headless,
coleta apenas PDFs de secoes regulatorias e institucionais, e baixa
para data/raw com rastreabilidade via manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from . import config

HEADERS = {
    "User-Agent": "TCC-RAG-UNESP/1.0 (pesquisa academica; coleta de documentos publicos)"
}
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
REQUEST_TIMEOUT = 30
POLITE_DELAY = 1.5
JS_WAIT_S = 6

# ── Filtros de URL para PDFs ─────────────────────────────────────────────────
# Padroes no nome/caminho do arquivo que indicam documentos IRRELEVANTES.
# Qualquer PDF cujo URL contenha uma dessas strings (case-insensitive) e ignorado.
PDF_BLOCKLIST = [
    "prova", "gabarito", "provao", "seriado",
    "resultado", "convocacao", "convocação", "inscri",
    "transferencia", "transferência", "portador",
    "fatec", "unicamp", "univesp", "usp_",
    "seed", "seduc", "ceeteps",
    "rec_insc", "rec_result", "retificacao_do_edital",
    "chamada", "matricula_port",
    "_ext_20", "_int_20",        # padroes de transferencia externa/interna com ano
]

# Secoes do site que NAO devem ser navegadas (economiza tempo e evita lixo).
PAGE_BLOCKLIST = [
    "/graduacao/transferencia", "/graduacao/vestibular",
    "/graduacao/provao", "/portador", "provao-paulista",
    "fatec", "unicamp", "seduc", "/concurso",
    "upload/graduacao/transferencia",
]

# Secoes relevantes: o crawler prioriza (e limita-se a) estas.
# Se vazio, navega em todo o dominio permitido.
PAGE_ALLOWLIST = [
    "fc.unesp.br",   # dominio principal
]

# Documentos conhecidos que devem ser baixados diretamente (independente do crawl).
KNOWN_DOCS = [
    "https://www2.unesp.br/Home/compilacao-legislacao-2020-27-08.pdf",
]


def _is_blocked_pdf(url: str) -> bool:
    url_lower = url.lower()
    return any(p in url_lower for p in PDF_BLOCKLIST)


def _is_blocked_page(url: str) -> bool:
    url_lower = url.lower()
    return any(p in url_lower for p in PAGE_BLOCKLIST)


def _slug_from_url(url: str) -> str:
    name = Path(urlparse(url).path).name or "documento.pdf"
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def _load_manifest() -> dict:
    path = config.DATA_RAW / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _save_manifest(manifest: dict) -> None:
    (config.DATA_RAW / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _download_pdf(url: str, manifest: dict) -> bool:
    if url in manifest:
        return False
    if _is_blocked_pdf(url):
        print(f"  [ignorado] {url.split('/')[-1][:60]}  (bloqueado por filtro)")
        return False
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [erro download] {url}: {exc}")
        return False

    content = resp.content
    if not content[:5].startswith(b"%PDF"):
        print(f"  [aviso] nao e PDF valido: {url.split('/')[-1][:60]}")
        return False

    filename = _slug_from_url(url)
    dest = config.DATA_RAW / filename
    if dest.exists():
        digest = hashlib.sha1(url.encode()).hexdigest()[:8]
        dest = config.DATA_RAW / f"{dest.stem}_{digest}{dest.suffix}"

    dest.write_bytes(content)
    manifest[url] = {
        "filename": dest.name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    print(f"  [ok] {dest.name}  ({len(content)//1024} KB)")
    return True


def crawl(
    seeds: list[str] | None = None,
    max_depth: int | None = None,
) -> dict:
    """Percorre o portal fc.unesp.br e baixa PDFs regulatorios/institucionais."""
    seeds = seeds or config.SCRAPER_SEEDS
    max_depth = config.SCRAPER_MAX_DEPTH if max_depth is None else max_depth

    if not seeds:
        raise ValueError("Nenhuma URL-semente configurada. Defina SCRAPER_SEEDS no .env.")

    manifest = _load_manifest()
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque((s, 0) for s in seeds)
    n_pdfs = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME_PATH)
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            ignore_https_errors=True,
        )
        context.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ("image", "media", "font", "stylesheet")
            else route.continue_(),
        )
        page = context.new_page()

        while queue:
            url, depth = queue.popleft()
            if url in visited or _is_blocked_page(url):
                continue
            visited.add(url)

            # Restringe ao dominio fc.unesp.br
            if "fc.unesp.br" not in urlparse(url).netloc:
                continue

            try:
                print(f"[nivel {depth}] {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(JS_WAIT_S)
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except PWTimeout:
                    pass
            except (PWTimeout, Exception) as exc:
                print(f"  [erro] {exc}")
                continue

            hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")

            for href in hrefs:
                href = href.split("#")[0].strip() if ".pdf" not in href.lower() else href
                if not href.startswith("http"):
                    continue
                if href.lower().endswith(".pdf"):
                    if _download_pdf(href, manifest):
                        n_pdfs += 1
                        _save_manifest(manifest)
                        time.sleep(POLITE_DELAY)
                elif depth < max_depth and "fc.unesp.br" in href:
                    if href not in visited and not _is_blocked_page(href):
                        queue.append((href, depth + 1))

        context.close()
        browser.close()

    # Baixa documentos conhecidos independente do crawl
    print("\n[documentos conhecidos]")
    for url in KNOWN_DOCS:
        if _download_pdf(url, manifest):
            n_pdfs += 1
            _save_manifest(manifest)
            time.sleep(POLITE_DELAY)

    _save_manifest(manifest)
    print(f"\nConcluido. {n_pdfs} novos PDFs baixados. Total no manifesto: {len(manifest)}.")
    return manifest


if __name__ == "__main__":
    crawl()
