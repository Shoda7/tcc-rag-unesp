"""Congela o corpus em um pacote verificavel (zip deterministico + somas SHA-256).

O pacote contem so as resolucoes (+ manifest.json). O conjunto de avaliacao (eval_set.json)
ainda vai mudar e sera publicado a parte, quando estiver final.

Gera:
    data/corpus_checksums.sha256   SHA-256 de cada arquivo do corpus (versionado no git)
    data/corpus_release.json       metadados e SHA-256 do pacote (versionado no git)
    dist/<nome>.zip                pacote para publicacao (NAO versionado)
    dist/<nome>.zip.sha256

O zip e montado com ordem fixa e datas fixas, entao os bytes dependem so do conteudo
dos arquivos (e da versao do zlib). Para verificar uma copia do corpus, compare os
arquivos com data/corpus_checksums.sha256:

    python scripts/snapshot_corpus.py --verificar

Uso:
    python scripts/snapshot_corpus.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEG = ROOT / "data" / "legislacao"
CHECKSUMS = ROOT / "data" / "corpus_checksums.sha256"
RELEASE = ROOT / "data" / "corpus_release.json"
DIST = ROOT / "dist"
NOME = "corpus-resolucoes-unesp-2016-2026"
FIXED_DATE = (2026, 1, 1, 0, 0, 0)

README = """# Corpus de resoluções da UNESP (2016–2026)

Texto integral de {n_docs} resoluções da Universidade Estadual Paulista "Júlio de Mesquita Filho"
(UNESP), usado no TCC "Implementação e avaliação de um sistema de Recuperação Aumentada por Geração
(RAG) para consulta de documentos regulatórios da UNESP Bauru" (Matheus Shoda Lima e Rafael
Panhozzi Rubio, Bacharelado em Sistemas de Informação, UNESP Bauru).

## Origem

- Fonte: base de resoluções do sistema de legislação da UNESP,
  https://sistemas.unesp.br/legislacao-web/ (base "R").
- Período das resoluções: 2016 a 2026. Portarias e documentos anteriores a 2016 não foram coletados.
- Coleta: scraper em Python (requests + BeautifulSoup) entre {coleta_inicio} e {coleta_fim},
  com intervalo de 1,2 s entre requisições. O texto de cada resolução é o conteúdo do elemento
  `div.painelTexto`, salvo em UTF-8 sem nenhum outro processamento.
- Os atos oficiais (resoluções) não são objeto de proteção de direito autoral no Brasil
  (Lei 9.610/1998, art. 8º, IV). Mesmo assim, o texto vigente e oficial deve ser consultado na fonte.

## Conteúdo

- `legislacao/resolucao_AAAA_NNNN.txt`: uma resolução por arquivo (AAAA = ano, NNNN = número).
- `legislacao/manifest.json`: metadados da coleta (número, ano, data do documento, título, nº de caracteres).
- `SHA256SUMS`: soma SHA-256 de cada arquivo (`sha256sum -c SHA256SUMS` verifica o pacote).

## Estatísticas

- Documentos: {n_docs}
- Palavras: {n_words} (mediana de {mediana} por documento; mínimo {minimo}; máximo {maximo})
- Por ano: {por_ano}

## Como citar

LIMA, Matheus Shoda; RUBIO, Rafael Panhozzi. Corpus de resoluções da UNESP (2016–2026) para avaliação
de sistemas RAG. 2026. Conjunto de dados.
"""


def br(x: float) -> str:
    """Numero inteiro com ponto como separador de milhar (padrao brasileiro)."""
    return f"{round(x):,}".replace(",", ".")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def arquivos_do_corpus() -> list[tuple[str, Path]]:
    """(nome dentro do pacote, caminho) em ordem fixa."""
    itens = [(f"legislacao/{p.name}", p) for p in sorted(LEG.glob("resolucao_*.txt"))]
    itens.append(("legislacao/manifest.json", LEG / "manifest.json"))
    return itens


def escrever_checksums(itens) -> dict[str, str]:
    soma = {nome: sha256(p) for nome, p in itens}
    CHECKSUMS.write_text(
        "".join(f"{h}  {nome}\n" for nome, h in sorted(soma.items())), encoding="utf-8", newline="\n"
    )
    return soma


def verificar() -> int:
    esperado = {}
    for linha in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        h, nome = linha.split("  ", 1)
        esperado[nome] = h
    erros = 0
    for nome, p in arquivos_do_corpus():
        if nome not in esperado:
            print(f"[fora da lista] {nome}")
            erros += 1
        elif not p.exists() or sha256(p) != esperado[nome]:
            print(f"[diferente] {nome}")
            erros += 1
    faltando = set(esperado) - {n for n, _ in arquivos_do_corpus()}
    for nome in sorted(faltando):
        print(f"[ausente] {nome}")
        erros += 1
    print("OK: corpus identico ao congelado." if not erros else f"{erros} divergencia(s).")
    return 1 if erros else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verificar", action="store_true", help="so confere o corpus atual com data/corpus_checksums.sha256")
    args = ap.parse_args()
    if args.verificar:
        return verificar()

    itens = arquivos_do_corpus()
    txts = [p for nome, p in itens if nome.startswith("legislacao/resolucao_")]
    palavras = sorted(len(p.read_text(encoding="utf-8").split()) for p in txts)
    n = len(palavras)
    mtimes = [datetime.fromtimestamp(p.stat().st_mtime) for p in txts]
    por_ano: dict[str, int] = {}
    for p in txts:
        ano = p.name.split("_")[1]
        por_ano[ano] = por_ano.get(ano, 0) + 1

    soma = escrever_checksums(itens)
    readme = README.format(
        n_docs=n,
        coleta_inicio=min(mtimes).strftime("%d/%m/%Y"),
        coleta_fim=max(mtimes).strftime("%d/%m/%Y"),
        n_words=br(sum(palavras)),
        mediana=br(statistics.median(palavras)), minimo=br(palavras[0]), maximo=br(palavras[-1]),
        por_ano=", ".join(f"{a}: {c}" for a, c in sorted(por_ano.items())),
    )

    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"{NOME}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        def add(nome: str, dados: bytes) -> None:
            zi = zipfile.ZipInfo(nome, FIXED_DATE)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, dados, compresslevel=9)
        add("README.md", readme.encode("utf-8"))
        add("SHA256SUMS", CHECKSUMS.read_bytes())
        for nome, p in itens:
            add(nome, p.read_bytes())

    zip_hash = sha256(zip_path)
    (DIST / f"{NOME}.zip.sha256").write_text(f"{zip_hash}  {zip_path.name}\n", encoding="utf-8", newline="\n")
    RELEASE.write_text(json.dumps({
        "pacote": zip_path.name,
        "sha256_pacote": zip_hash,
        "tamanho_bytes": zip_path.stat().st_size,
        "documentos": n,
        "palavras": sum(palavras),
        "arquivos_no_pacote": len(itens) + 2,
        "sha256_do_arquivo_de_somas": hashlib.sha256(CHECKSUMS.read_bytes()).hexdigest(),
        "coleta": {"inicio": min(mtimes).date().isoformat(), "fim": max(mtimes).date().isoformat()},
        "fonte": "https://sistemas.unesp.br/legislacao-web/ (base R)",
        "publicado_em": None,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"documentos: {n}   palavras: {sum(palavras)}")
    print(f"pacote: {zip_path}  ({zip_path.stat().st_size / 1e6:.1f} MB)")
    print(f"sha256: {zip_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
