"""Extracao e limpeza de texto dos PDFs baixados.

Le os PDFs de data/raw, extrai o texto com pdfplumber, aplica limpeza
(remocao de cabecalhos/rodapes repetidos, normalizacao de espacos) e salva
o texto limpo em data/processed/<nome>.txt.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber

from . import config


def _normalize(text: str) -> str:
    """Normaliza encoding, espacos e quebras de linha."""
    text = unicodedata.normalize("NFC", text)
    # Une palavras quebradas por hifen no fim da linha: "regula-\nmento" -> "regulamento"
    text = re.sub(r"-\n(\w)", r"\1", text)
    # Quebras simples viram espaco; quebras duplas (paragrafo) sao preservadas
    text = re.sub(r"\n{2,}", " ", text)   # marca temporaria de paragrafo
    text = re.sub(r"\s*\n\s*", " ", text)
    text = text.replace(" ", "\n\n")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _remove_repeated_lines(pages: list[str]) -> list[str]:
    """Remove linhas que se repetem em muitas paginas (cabecalho/rodape)."""
    line_counts: Counter[str] = Counter()
    for page in pages:
        for line in page.splitlines():
            stripped = line.strip()
            if stripped:
                line_counts[stripped] += 1

    threshold = max(3, int(len(pages) * 0.5))  # aparece em >=50% das paginas
    boilerplate = {ln for ln, c in line_counts.items() if c >= threshold}

    cleaned = []
    for page in pages:
        kept = [
            ln for ln in page.splitlines()
            if ln.strip() not in boilerplate
            and not re.fullmatch(r"\s*\d+\s*", ln)  # numeros de pagina isolados
        ]
        cleaned.append("\n".join(kept))
    return cleaned


def extract_pdf(pdf_path: Path) -> str:
    """Extrai e limpa o texto de um unico PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        pages = [(p.extract_text() or "") for p in pdf.pages]
    pages = _remove_repeated_lines(pages)
    full = "\n\n".join(pages)
    return _normalize(full)


def extract_all() -> list[Path]:
    """Processa todos os PDFs de data/raw. Retorna os caminhos .txt gerados."""
    pdfs = sorted(config.DATA_RAW.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF encontrado em {config.DATA_RAW}.")
        return []

    outputs = []
    for pdf in pdfs:
        print(f"Extraindo: {pdf.name}")
        try:
            text = extract_pdf(pdf)
        except Exception as exc:  # noqa: BLE001 - log e segue
            print(f"  [erro] {pdf.name}: {exc}")
            continue
        if not text.strip():
            print(f"  [aviso] {pdf.name} sem texto extraivel (PDF escaneado? precisa de OCR).")
            continue
        out = config.DATA_PROCESSED / f"{pdf.stem}.txt"
        out.write_text(text, encoding="utf-8")
        outputs.append(out)
        print(f"  [ok] {out.name}  ({len(text)} caracteres)")

    print(f"\n{len(outputs)} documentos processados.")
    return outputs


if __name__ == "__main__":
    extract_all()
