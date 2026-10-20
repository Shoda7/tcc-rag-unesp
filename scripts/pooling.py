"""Gera as planilhas de julgamento de relevancia por pooling.

Para cada consulta de data/eval_set.json, junta (pool) os 5 primeiros documentos de cada um dos
4 metodos de recuperacao, mais o documento de referencia atual, e exporta uma planilha por
anotador. O metodo que recuperou cada documento NAO aparece na planilha (julgamento as cegas) e
a ordem dos documentos e embaralhada de forma diferente para cada anotador.

Saidas (data/julgamentos/):
    pool.json                       qual metodo recuperou cada documento (NAO abrir antes de anotar;
                                    e usado pela etapa de reavaliacao)
    julgamento_<anotador>.xlsx      planilha de cada anotador

Uso:
    python scripts/pooling.py
    python scripts/pooling.py --anotadores matheus rafael --prof 5
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import evaluate  # noqa: E402  (scripts/evaluate.py: retrieve, top_documents, METHODS)
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

from src import db  # noqa: E402
from src.embeddings import embed_query  # noqa: E402

LEG = ROOT / "data" / "legislacao"
OUT = ROOT / "data" / "julgamentos"
BASE_URL = "https://sistemas.unesp.br/legislacao-web/"
MAX_EMENTA = 450
MAX_TRECHO = 800


def ementa(source: str) -> str:
    """Titulo + ementa: linhas iniciais ate o preambulo ('O REITOR ...')."""
    linhas = (LEG / source).read_text(encoding="utf-8").splitlines()
    partes: list[str] = []
    for ln in linhas[:8]:
        ln = ln.strip()
        if re.match(r"^(O|A)\s*(REITOR|REITORA)\b", ln) or ln in ("O", "A"):
            break
        if ln:
            partes.append(ln)
    texto = re.sub(r"\s+", " ", " ".join(partes)).strip()
    return texto[:MAX_EMENTA] + ("…" if len(texto) > MAX_EMENTA else "")


def link_oficial(source: str, manifest: dict) -> str:
    m = re.match(r"resolucao_(\d{4})_(\d{4})\.txt", source)
    meta = manifest.get(f"R_{m.group(1)}_{m.group(2)}") if m else None
    if not meta:
        return ""
    return (f"{BASE_URL}?base=R&numero={quote(meta['numero'])}&ano={meta['ano']}"
            f"&dataDocumento={quote(meta['data_doc'], safe='/')}")


def construir_pool(prof: int) -> dict:
    """Pool por consulta: {qid: {query, type, docs: {source: {metodo: posicao_no_ranking_de_documentos}}, trechos}}"""
    consultas = json.loads((ROOT / "data" / "eval_set.json").read_text("utf-8"))
    conn = db.connect()
    embed_query("aquecimento")
    for m in evaluate.METHODS:
        evaluate.retrieve(conn, m, "aquecimento", embed_query("aquecimento"))

    pool: dict[str, dict] = {}
    for q in consultas:
        qvec = embed_query(q["query"])
        docs: dict[str, dict[str, int]] = {}
        trechos: dict[str, tuple[int, str]] = {}   # melhor (menor rank de chunk) trecho por documento
        for m in evaluate.METHODS:
            resultados = evaluate.retrieve(conn, m, q["query"], qvec)
            for pos, source in enumerate(evaluate.top_documents(resultados, prof), 1):
                docs.setdefault(source, {})[m] = pos
            for rank, r in enumerate(resultados, 1):
                if r["source"] in docs and (r["source"] not in trechos or rank < trechos[r["source"]][0]):
                    trechos[r["source"]] = (rank, r["content"])
        for source in q["relevant_sources"]:         # referencia atual entra no pool de qualquer forma
            docs.setdefault(source, {})
        pool[q["id"]] = {"query": q["query"], "type": q.get("type", ""),
                         "referencia_atual": q["relevant_sources"], "docs": docs,
                         "trechos": {s: t[1] for s, t in trechos.items()}}
    conn.close()
    return pool


def trecho_de(pool_q: dict, source: str) -> str:
    texto = pool_q["trechos"].get(source)
    if texto is None:  # documento so entrou como referencia: mostra o comeco do corpo
        texto = " ".join((LEG / source).read_text(encoding="utf-8").split()[:130])
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:MAX_TRECHO] + ("…" if len(texto) > MAX_TRECHO else "")


def escrever_planilha(path: Path, anotador: str, pool: dict, seed: int) -> int:
    manifest = json.loads((LEG / "manifest.json").read_text("utf-8"))
    rng = random.Random(seed)
    wb = Workbook()

    ws0 = wb.active
    ws0.title = "Instruções"
    ws0.column_dimensions["A"].width = 110
    linhas = [
        (f"Julgamento de relevância — anotador: {anotador}", Font(bold=True, size=14)),
        ("", None),
        ("Para cada linha da aba 'Julgamentos', preencha a coluna F com 0, 1 ou 2:", Font(bold=True)),
        ("  2 = o documento RESPONDE à pergunta (a informação principal está nele).", None),
        ("  1 = o documento trata do tema e traz informação útil, mas não responde por completo.", None),
        ("  0 = o documento não ajuda a responder a pergunta.", None),
        ("", None),
        ("Regras:", Font(bold=True)),
        ("  • Julgue o DOCUMENTO, não só o trecho mostrado. Se tiver dúvida, abra o link oficial (coluna H).", None),
        ("  • Anote sozinho(a), sem conversar com a outra pessoa, e sem procurar saber qual sistema trouxe cada documento.", None),
        ("  • Julgue cada documento de forma independente: vários documentos da mesma consulta podem ser 2.", None),
        ("  • Use a coluna G só para dúvidas ou casos de fronteira (ex.: 'versão antiga da norma').", None),
        ("  • Não altere as colunas A–E nem a ordem das linhas. Salve o arquivo a cada consulta.", None),
        ("", None),
        ("Progresso:", Font(bold=True)),
    ]
    for i, (texto, fonte) in enumerate(linhas, 1):
        c = ws0.cell(row=i, column=1, value=texto)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if fonte:
            c.font = fonte

    ws = wb.create_sheet("Julgamentos")
    cab = ["ID", "Consulta", "Documento", "Início do documento (título e ementa)", "Trecho do documento",
           "Relevância (0/1/2)", "Observação", "Link oficial"]
    larg = [10, 38, 24, 48, 70, 12, 28, 30]
    for j, (t, w) in enumerate(zip(cab, larg), 1):
        c = ws.cell(row=1, column=j, value=t)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[1].height = 34
    ws.freeze_panes = "C2"

    r = 2
    for qid in sorted(pool):
        pq = pool[qid]
        fontes = list(pq["docs"])
        rng.shuffle(fontes)
        for k, source in enumerate(fontes, 1):
            valores = [f"{qid}-{k:02d}", pq["query"], source, ementa(source), trecho_de(pq, source), None, None,
                       link_oficial(source, manifest)]
            for j, v in enumerate(valores, 1):
                c = ws.cell(row=r, column=j, value=v)
                c.alignment = Alignment(wrap_text=True, vertical="top",
                                        horizontal="center" if j in (1, 6) else "left")
                if j == 6:
                    c.fill = PatternFill("solid", fgColor="FFF2CC")
                    c.font = Font(bold=True, size=12)
                if j == 8 and v:
                    c.hyperlink = v
                    c.font = Font(color="0563C1", underline="single")
            # altura explicita: nem todo leitor de planilha ajusta sozinho linhas com quebra de texto
            linhas_txt = max(math.ceil(len(str(v or "")) / (w * 1.15)) for v, w in zip(valores[:5], larg[:5]))
            ws.row_dimensions[r].height = min(max(30, 12.5 * linhas_txt + 8), 190)
            r += 1
    total = r - 2
    dv = DataValidation(type="list", formula1='"0,1,2"', allow_blank=True, showErrorMessage=True,
                        errorTitle="Valor inválido", error="Use 0, 1 ou 2.")
    ws.add_data_validation(dv)
    dv.add(f"F2:F{r - 1}")
    ws.auto_filter.ref = f"A1:H{r - 1}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"

    ws0.cell(row=len(linhas) + 1, column=1,
             value=f'=COUNTA(Julgamentos!F2:F{r - 1})&" de {total} julgamentos preenchidos"')
    wb.save(path)
    return total


def ja_anotada(path: Path) -> int:
    """Quantas notas ja existem na coluna F da planilha (0 se nao existir)."""
    if not path.exists():
        return 0
    from openpyxl import load_workbook
    ws = load_workbook(path, read_only=True)["Julgamentos"]
    return sum(1 for row in ws.iter_rows(min_row=2, min_col=6, max_col=6, values_only=True) if row[0] is not None)


def main() -> None:
    ap = argparse.ArgumentParser(description="Pooling para julgamento de relevancia")
    ap.add_argument("--anotadores", nargs="+", default=["matheus", "rafael"])
    ap.add_argument("--prof", type=int, default=5, help="profundidade por metodo (documentos)")
    ap.add_argument("--forcar", action="store_true", help="sobrescreve planilhas mesmo que ja tenham notas")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    for nome in args.anotadores:
        n = ja_anotada(OUT / f"julgamento_{nome}.xlsx")
        if n and not args.forcar:
            sys.exit(f"RECUSADO: julgamento_{nome}.xlsx ja tem {n} nota(s) preenchida(s). "
                     "Gerar de novo apagaria esse trabalho. Use --forcar se for isso mesmo que quer.")
    pool = construir_pool(args.prof)
    (OUT / "pool.json").write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")

    tamanhos = [len(p["docs"]) for p in pool.values()]
    print(f"consultas: {len(pool)}   documentos por consulta: min {min(tamanhos)}, "
          f"media {sum(tamanhos) / len(tamanhos):.1f}, max {max(tamanhos)}   total de julgamentos: {sum(tamanhos)}")
    for i, nome in enumerate(args.anotadores):
        n = escrever_planilha(OUT / f"julgamento_{nome}.xlsx", nome, pool, seed=1000 + i)
        print(f"  {nome}: {n} linhas -> {OUT / f'julgamento_{nome}.xlsx'}")


if __name__ == "__main__":
    main()
