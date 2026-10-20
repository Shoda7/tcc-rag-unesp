"""Gera as planilhas de anotacao (as cegas) das respostas do experimento de geracao.

Le data/geracao/respostas.jsonl e produz, em data/geracao/:
    anotacao_<anotador>.xlsx   uma planilha por anotador (condicao oculta, ordem embaralhada)
    chave_condicoes.json       qual condicao gerou cada linha (NAO abrir antes de anotar)

Cada linha e uma resposta (pergunta x condicao). Criterios (ver GUIA_ANOTACAO_GERACAO.md):
correcao (0/1/2), alucinacao (Sim/Nao), citacao correta e recusa adequada.

Uso:
    python scripts/preparar_anotacao_geracao.py
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pooling  # noqa: E402  (scripts/pooling.py: ementa, link_oficial)
from openpyxl import Workbook, load_workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

from src import db  # noqa: E402

GER = ROOT / "data" / "geracao"
LEG = ROOT / "data" / "legislacao"
CITACAO = re.compile(r"resolucao_\d{4}_\d{4}\.txt")
# "Resolução UNESP nº 23/2018", "Res. 23/2018", "Resolução 2021/0022"
CITACAO_PROSA = re.compile(r"Resolu[çc][ãa]o(?:\s+UNESP)?\s*(?:n[º°o\.]*\s*)?(\d{1,4})\s*/\s*(\d{4})|\bRes\.\s*(\d{1,4})\s*/\s*(\d{4})")


def fontes_mencionadas(texto: str) -> list[str]:
    """Arquivos de resolucao citados na resposta, pelo nome do arquivo ou em prosa; so os que existem."""
    achados = set(CITACAO.findall(texto))
    for m in CITACAO_PROSA.finditer(texto):
        a, b = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        numero, ano = (b, a) if len(a) == 4 else (a, b)   # "2021/0022" vem invertido
        arq = f"resolucao_{ano}_{int(numero):04d}.txt"
        if (LEG / arq).exists():
            achados.add(arq)
    return sorted(achados)
TIPO_ROTULO = {"respondivel": "respondível", "sem_resposta": "SEM resposta no corpus"}

COLUNAS = [
    ("ID", 9), ("Pergunta", 34), ("Tipo da pergunta", 14), ("Resposta do sistema", 90),
    ("Referência (resposta esperada / documento)", 55), ("Resoluções mencionadas na resposta", 26),
    ("Links oficiais (resoluções mencionadas)", 30),
    ("Correção (0/1/2/N/A)", 12), ("Alucinação (Sim/Não)", 12), ("Citação correta (Sim/Não/N/A)", 13),
    ("Recusa adequada (Sim/Não/N/A)", 13), ("Observação", 30),
]
ENTRADA = {"H": "0,1,2,N/A", "I": "Sim,Não", "J": "Sim,Não,N/A", "K": "Sim,Não,N/A"}


def referencia(q: dict, conn, manifest: dict) -> str:
    """Texto de referencia mostrado ao anotador (sem revelar a condicao)."""
    if q["tipo"] == "sem_resposta":
        return q["resposta_referencia"]
    partes = []
    if q.get("resposta_referencia"):
        partes.append("RESPOSTA ESPERADA: " + q["resposta_referencia"])
    for src in q["fontes"]:
        partes.append(f"DOCUMENTO DE REFERÊNCIA: {src}\n{pooling.ementa(src)}")
        if not q.get("resposta_referencia"):
            trecho = melhor_trecho(conn, q["pergunta"], src)
            if trecho:
                partes.append("TRECHO MAIS PRÓXIMO DA PERGUNTA: " + trecho)
        partes.append("Link: " + pooling.link_oficial(src, manifest))
    return "\n\n".join(partes)


def melhor_trecho(conn, pergunta: str, source: str) -> str:
    for r in db.search_bm25(conn, pergunta, k=200):
        if r["source"] == source:
            t = re.sub(r"\s+", " ", r["content"]).strip()
            return t[:900] + ("…" if len(t) > 900 else "")
    return ""


def escrever(path: Path, nome: str, linhas: list[dict]) -> None:
    wb = Workbook()
    ws0 = wb.active
    ws0.title = "Instruções"
    ws0.column_dimensions["A"].width = 120
    instr = [
        (f"Anotação das respostas geradas — anotador: {nome}", Font(bold=True, size=14)),
        ("", None),
        ("Leia o guia GUIA_ANOTACAO_GERACAO.md antes de começar. Resumo dos critérios (preencha as colunas H a K):", Font(bold=True)),
        ("  H — Correção: 2 = correta e completa; 1 = parcialmente correta; 0 = errada, não responde ou recusa sem motivo. N/A nas perguntas SEM resposta.", None),
        ("  I — Alucinação: Sim se houver afirmação específica (número, data, artigo, procedimento) que não está nas resoluções ou que as contradiz.", None),
        ("  J — Citação correta: se a resposta cita arquivos [resolucao_...txt], Sim quando o documento citado traz mesmo aquela informação; N/A se não citar nenhum.", None),
        ("  K — Recusa adequada (só perguntas SEM resposta): Sim = disse que não encontrou/não sabe, sem inventar; Não = inventou. N/A nas respondíveis.", None),
        ("", None),
        ("Anote sozinho(a), sem conversar com a outra pessoa. Não tente descobrir de qual sistema veio cada resposta.", Font(bold=True)),
        ("Não altere as colunas A–G nem a ordem das linhas. Salve a cada pergunta.", None),
        ("", None),
        ("Progresso:", Font(bold=True)),
    ]
    for i, (t, f) in enumerate(instr, 1):
        c = ws0.cell(row=i, column=1, value=t)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if f:
            c.font = f

    ws = wb.create_sheet("Respostas")
    for j, (t, w) in enumerate(COLUNAS, 1):
        c = ws.cell(row=1, column=j, value=t)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[1].height = 48
    ws.freeze_panes = "C2"

    for r, ln in enumerate(linhas, 2):
        valores = [ln["item"], ln["pergunta"], TIPO_ROTULO[ln["tipo"]], ln["resposta"], ln["referencia"],
                   ln["citadas"], ln["links"], None, None, None, None, None]
        for j, v in enumerate(valores, 1):
            c = ws.cell(row=r, column=j, value=v)
            c.alignment = Alignment(wrap_text=True, vertical="top", horizontal="center" if j in (1, 3, 8, 9, 10, 11) else "left")
            if j >= 8 and j <= 11:
                c.fill = PatternFill("solid", fgColor="FFF2CC")
                c.font = Font(bold=True, size=11)
            if j == 7 and v:
                c.hyperlink = v.splitlines()[0]
                c.font = Font(color="0563C1", underline="single")
        n_lin = max(math.ceil(len(str(v or "")) / (w * 1.15)) + str(v or "").count("\n")
                    for v, (_, w) in zip(valores[:7], COLUNAS[:7]))
        ws.row_dimensions[r].height = min(max(40, 12.5 * n_lin + 8), 400)
    ultima = len(linhas) + 1
    for col, lista in ENTRADA.items():
        dv = DataValidation(type="list", formula1=f'"{lista}"', allow_blank=True, showErrorMessage=True,
                            errorTitle="Valor inválido", error=f"Use: {lista}")
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{ultima}")
    ws.auto_filter.ref = f"A1:L{ultima}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    ws0.cell(row=len(instr) + 1, column=1,
             value=f'=COUNTA(Respostas!H2:H{ultima})&" de {len(linhas)} respostas com correção preenchida"')
    wb.save(path)


def ja_anotada(path: Path) -> int:
    if not path.exists():
        return 0
    ws = load_workbook(path, read_only=True)["Respostas"]
    return sum(1 for row in ws.iter_rows(min_row=2, min_col=8, max_col=11, values_only=True) if any(v is not None for v in row))


def main() -> None:
    ap = argparse.ArgumentParser(description="Planilhas de anotacao da geracao")
    ap.add_argument("--anotadores", nargs="+", default=["matheus", "rafael"])
    ap.add_argument("--forcar", action="store_true")
    args = ap.parse_args()

    for nome in args.anotadores:
        n = ja_anotada(GER / f"anotacao_{nome}.xlsx")
        if n and not args.forcar:
            sys.exit(f"RECUSADO: anotacao_{nome}.xlsx ja tem {n} linha(s) anotada(s). Use --forcar se for isso mesmo que quer.")

    perguntas = {q["id"]: q for q in json.loads((GER / "perguntas.json").read_text("utf-8"))}
    respostas = [json.loads(x) for x in (GER / "respostas.jsonl").read_text("utf-8").splitlines()]
    manifest = json.loads((LEG / "manifest.json").read_text("utf-8"))
    conn = db.connect()

    por_pergunta: dict[str, list[dict]] = {}
    for r in respostas:
        por_pergunta.setdefault(r["id"], []).append(r)
    incompletas = [qid for qid, rs in por_pergunta.items() if len(rs) < 3]
    if incompletas:
        print(f"aviso: perguntas com menos de 3 condicoes: {incompletas}")

    # identificador anonimo por resposta (fixo para os dois anotadores) e chave
    ids = [(r["id"], r["condicao"]) for r in respostas]
    rng_id = random.Random(7)
    codigos = rng_id.sample(range(100, 100 + len(ids) * 3), len(ids))
    item_de = {chave: f"R{codigos[i]}" for i, chave in enumerate(ids)}
    chave = {item_de[(r["id"], r["condicao"])]: {"pergunta_id": r["id"], "condicao": r["condicao"]} for r in respostas}

    refs = {qid: referencia(perguntas[qid], conn, manifest) for qid in por_pergunta}
    conn.close()

    for i, nome in enumerate(args.anotadores):
        rng = random.Random(2000 + i)
        linhas = []
        for qid in sorted(por_pergunta):
            rs = por_pergunta[qid][:]
            rng.shuffle(rs)
            for r in rs:
                citadas = fontes_mencionadas(r["answer"])
                links = [pooling.link_oficial(s, manifest) for s in citadas]
                linhas.append({
                    "item": item_de[(r["id"], r["condicao"])], "pergunta": perguntas[qid]["pergunta"],
                    "tipo": perguntas[qid]["tipo"], "resposta": r["answer"] or "(resposta vazia)",
                    "referencia": refs[qid], "citadas": "\n".join(citadas) or "(nenhuma)",
                    "links": "\n".join(l for l in links if l),
                })
        escrever(GER / f"anotacao_{nome}.xlsx", nome, linhas)
        print(f"  {nome}: {len(linhas)} linhas -> {GER / f'anotacao_{nome}.xlsx'}")
    (GER / "chave_condicoes.json").write_text(json.dumps(chave, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
