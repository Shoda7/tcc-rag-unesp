"""
Scraper do sistema de legislacao da UNESP (sistemas.unesp.br/legislacao-web).

Estrategia:
  1. Carrega a pagina principal e le a arvore de documentos do HTML.
  2. Para cada documento, constroi a URL ?base=R&numero=X&ano=Y&dataDocumento=DD/MM/YYYY.
  3. Extrai o texto do div.painelTexto e salva em data/legislacao/.
  4. Registra o progresso em data/legislacao/manifest.json (permite retomar).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "data" / "legislacao"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
BASE_URL = "https://sistemas.unesp.br/legislacao-web/"
HEADERS = {"User-Agent": "TCC-RAG-UNESP/1.0 (pesquisa academica; coleta de legislacao publica)"}
POLITE_DELAY = 1.2  # segundos entre requisicoes

MESES = {
    "JANEIRO": "01", "FEVEREIRO": "02", "MARCO": "03", "MARÇO": "03",
    "MARO": "03",   # MARÇO com Ç corrompido pelo encoding vira MARO apos strip
    "ABRIL": "04", "MAIO": "05", "JUNHO": "06", "JULHO": "07",
    "AGOSTO": "08", "SETEMBRO": "09", "OUTUBRO": "10",
    "NOVEMBRO": "11", "DEZEMBRO": "12",
}

LABEL_RE = re.compile(r"(\d+)\s*,\s*DE\s+(\d+)\s+DE\s+(\w+)\s+DE\s+(\d{4})", re.IGNORECASE)


def _parse_label(label: str) -> tuple[str, str, str] | None:
    """Retorna (numero, ano, dataDocumento) ou None se nao parsear."""
    m = LABEL_RE.search(label)
    if not m:
        return None
    numero, dia, mes_raw, ano = m.groups()
    mes_key = re.sub(r"[^A-Z]", "", mes_raw.upper()).replace("Ç", "C")
    mes = MESES.get(mes_key)
    if not mes:
        return None
    return numero, ano, f"{int(dia):02d}/{mes}/{ano}"


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def _save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _get_with_retry(url: str, timeout: int = 45, max_retries: int = 5) -> requests.Response:
    """GET com retry exponencial para lidar com instabilidade do servidor."""
    for attempt in range(1, max_retries + 1):
        try:
            return requests.get(url, headers=HEADERS, timeout=timeout)
        except (requests.RequestException, OSError) as exc:
            wait = 30 * attempt
            print(f"  [retry {attempt}/{max_retries}] {exc} — aguardando {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"Falha apos {max_retries} tentativas: {url}")


def _fetch_doc_list() -> list[dict]:
    """Le a arvore do site e retorna lista de {numero, ano, data_doc, label}."""
    print("Carregando arvore de documentos...")
    r = _get_with_retry(BASE_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    docs = []
    for span in soup.find_all("span", {"data-did": True}):
        label = span.get_text(strip=True)
        parsed = _parse_label(label)
        if parsed:
            numero, ano, data_doc = parsed
            docs.append({
                "did": span["data-did"],
                "numero": numero,
                "ano": ano,
                "data_doc": data_doc,
                "label": label,
            })
        else:
            print(f"  [aviso] nao parseou: {label!r}")

    print(f"  {len(docs)} documentos encontrados na arvore.")
    return docs


def _fetch_text(numero: str, ano: str, data_doc: str) -> str | None:
    """Busca o texto de um documento pelo numero/ano/data."""
    url = f"{BASE_URL}?base=R&numero={numero}&ano={ano}&dataDocumento={data_doc}"
    try:
        r = _get_with_retry(url)
        r.raise_for_status()
    except Exception as exc:
        print(f"    [erro http] {exc}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    panel = soup.find("div", {"class": lambda c: c and "painelTexto" in c})
    if not panel:
        print("    [aviso] div.painelTexto nao encontrado")
        return None

    text = panel.get_text(separator="\n", strip=True)
    # Descarta a pagina padrao (sem documento carregado)
    if len(text) < 500 or "Esta base de dados" in text[:200]:
        print("    [aviso] texto parece ser a pagina padrao (doc nao encontrado)")
        return None

    return text


def scrape(base: str = "R") -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()

    docs = _fetch_doc_list()
    total = len(docs)
    baixados = 0
    pulados = 0
    erros = 0

    for i, doc in enumerate(docs, 1):
        key = f"{base}_{doc['ano']}_{doc['numero'].zfill(4)}"
        if key in manifest:
            pulados += 1
            continue

        print(f"[{i}/{total}] Resolucao {doc['numero']}/{doc['ano']} ({doc['data_doc']})")
        text = _fetch_text(doc["numero"], doc["ano"], doc["data_doc"])

        if text:
            filename = f"resolucao_{doc['ano']}_{doc['numero'].zfill(4)}.txt"
            dest = OUTPUT_DIR / filename
            dest.write_text(text, encoding="utf-8")
            manifest[key] = {
                "filename": filename,
                "numero": doc["numero"],
                "ano": doc["ano"],
                "data_doc": doc["data_doc"],
                "label": doc["label"],
                "chars": len(text),
            }
            _save_manifest(manifest)
            baixados += 1
            print(f"  -> salvo ({len(text)} chars)")
        else:
            erros += 1

        time.sleep(POLITE_DELAY)

    print(f"\nConcluido. Baixados: {baixados} | Pulados (ja existiam): {pulados} | Erros: {erros}")
    print(f"Arquivos em: {OUTPUT_DIR}")


if __name__ == "__main__":
    scrape()
