"""Analisa a avaliacao da geracao (etapa 9): concordancia, consolidacao e comparacao das 3 condicoes.

Entradas (em data/geracao/, ou --dir):
    anotacao_<anotador>.xlsx     planilhas preenchidas (colunas H a K)
    chave_condicoes.json         condicao que gerou cada linha
    respostas.jsonl              respostas e metadados (tokens, latencia)
    perguntas.json               tipo e subtipo das perguntas
    divergencias_geracao.csv     (opcional) preenchido pelos autores: coluna valor_final

Saidas: divergencias_geracao.csv e resultados_geracao.json.

Criterios (ver GUIA_ANOTACAO_GERACAO.md):
    correcao (0/1/2)  so respondiveis      alucinacao (Sim/Nao)   todas
    citacao (Sim/Nao/N/A)                  recusa adequada (Sim/Nao/N/A) so sem resposta

Uso: python scripts/analisar_geracao.py
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from avaliar_julgamentos import kappa, sem_nan  # noqa: E402
from evaluate import bootstrap_ci, holm, randomization_test  # noqa: E402

CONDICOES = ["closed_book", "rag_vetorial", "rag_hibrido"]
NOME = {"closed_book": "Sem recuperação", "rag_vetorial": "RAG vetorial", "rag_hibrido": "RAG híbrido"}
CRITERIOS = ["correcao", "alucinacao", "citacao", "recusa"]
COLUNAS = {"correcao": 7, "alucinacao": 8, "citacao": 9, "recusa": 10}        # indices (0-based) das colunas H..K
PIOR = {"correcao": "0", "alucinacao": "Sim", "citacao": "Não", "recusa": "Não"}   # valor provisorio (pessimista)
VALIDOS = {"correcao": {"0", "1", "2", "N/A"}, "alucinacao": {"Sim", "Não"},
           "citacao": {"Sim", "Não", "N/A"}, "recusa": {"Sim", "Não", "N/A"}}


def ler(path: Path) -> dict[str, dict[str, str]]:
    ws = load_workbook(path, read_only=True, data_only=True)["Respostas"]
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        out[str(row[0])] = {c: ("" if row[i] is None else str(row[i]).strip()) for c, i in COLUNAS.items()}
    return out


def problemas(linhas: dict[str, dict[str, str]], tipos: dict[str, str]) -> list[str]:
    """Valores invalidos ou combinacoes incoerentes com o tipo da pergunta."""
    ruins = []
    for item, v in linhas.items():
        for c in CRITERIOS:
            if v[c] not in VALIDOS[c]:
                ruins.append(f"{item}:{c}='{v[c]}'")
        if tipos[item] == "respondivel" and (v["correcao"] == "N/A" or v["recusa"] != "N/A"):
            ruins.append(f"{item}: pergunta respondivel deve ter correcao 0/1/2 e recusa N/A")
        if tipos[item] == "sem_resposta" and (v["correcao"] != "N/A" or v["recusa"] == "N/A"):
            ruins.append(f"{item}: pergunta SEM resposta deve ter correcao N/A e recusa Sim/Nao")
    return ruins


def ic(x) -> list[float]:
    return list(bootstrap_ci(list(x))) if len(x) else [float("nan")] * 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(ROOT / "data" / "geracao"))
    ap.add_argument("--anotadores", nargs="+", default=["matheus", "rafael"])
    ap.add_argument("--permitir-divergencias", action="store_true", help="usa o valor pessimista onde nao ha valor_final (PROVISORIO)")
    args = ap.parse_args()
    d = Path(args.dir)

    chave = json.loads((d / "chave_condicoes.json").read_text("utf-8"))
    perguntas = {q["id"]: q for q in json.loads((d / "perguntas.json").read_text("utf-8"))}
    respostas = {(r["id"], r["condicao"]): r for r in map(json.loads, (d / "respostas.jsonl").read_text("utf-8").splitlines())}
    planilhas = [ler(d / f"anotacao_{a}.xlsx") for a in args.anotadores]
    tipos = {item: perguntas[c["pergunta_id"]]["tipo"] for item, c in chave.items()}

    erros = [f"{a}: {p}" for a, pl in zip(args.anotadores, planilhas) for p in problemas(pl, tipos)]
    if erros or any(set(pl) != set(chave) for pl in planilhas):
        print("RECUSADO: planilhas incompletas ou invalidas.")
        for e in erros[:25]:
            print("  ", e)
        if len(erros) > 25:
            print(f"   ... e mais {len(erros) - 25}")
        return 1

    itens = sorted(chave)
    # concordancia por criterio
    conc = {}
    for c in CRITERIOS:
        pares = [(pl_a[i][c], pl_b[i][c]) for i in itens for pl_a, pl_b in [planilhas] if pl_a[i][c] != "N/A" or pl_b[i][c] != "N/A"]
        if not pares:
            continue
        cats = sorted({v for p in pares for v in p})
        idx = {v: k for k, v in enumerate(cats)}
        a = [idx[x] for x, _ in pares]
        b = [idx[y] for _, y in pares]
        conc[c] = {"n": len(pares), "concordancia_simples": float(np.mean([x == y for x, y in pares])),
                   "kappa": kappa(a, b, categorias=len(cats)),
                   **({"kappa_ponderado_quadratico": kappa(a, b, "quadratico", len(cats))} if c == "correcao" else {})}

    # divergencias e consolidacao
    div_path = d / "divergencias_geracao.csv"
    decididas = {}
    if div_path.exists():
        for r in csv.DictReader(open(div_path, encoding="utf-8-sig")):
            if r["valor_final"].strip():
                decididas[(r["item"], r["criterio"])] = r["valor_final"].strip()
    divs = [(i, c) for i in itens for c in CRITERIOS if planilhas[0][i][c] != planilhas[1][i][c]]
    with open(div_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item", "criterio", "pergunta", *[f"valor_{a}" for a in args.anotadores], "valor_final"])
        for i, c in divs:
            w.writerow([i, c, perguntas[chave[i]["pergunta_id"]]["pergunta"], planilhas[0][i][c], planilhas[1][i][c], decididas.get((i, c), "")])
    pendentes = [x for x in divs if x not in decididas]
    if pendentes and not args.permitir_divergencias:
        print(f"{len(divs)} divergencias; {len(pendentes)} sem decisao. Preencham valor_final em {div_path} e rodem de novo "
              "(ou --permitir-divergencias para um resultado provisorio).")
        return 2

    final = {i: {c: decididas.get((i, c), planilhas[0][i][c] if planilhas[0][i][c] == planilhas[1][i][c] else PIOR[c]) for c in CRITERIOS} for i in itens}

    # tabela por (pergunta, condicao)
    reg = {}
    for i in itens:
        qid, cond = chave[i]["pergunta_id"], chave[i]["condicao"]
        # perguntas.json é a fonte do tipo; vem por último para não ser sobrescrito pelo campo gravado na resposta
        reg[(qid, cond)] = {**respostas[(qid, cond)], **final[i], "tipo": perguntas[qid]["tipo"], "subtipo": perguntas[qid].get("subtipo")}

    def resumo(cond: str) -> dict:
        resp = [v for (q, c), v in reg.items() if c == cond and v["tipo"] == "respondivel"]
        sem = [v for (q, c), v in reg.items() if c == cond and v["tipo"] == "sem_resposta"]
        todas = resp + sem
        cita = [v for v in todas if v["citacao"] != "N/A"]
        corr = [int(v["correcao"]) for v in resp]
        out = {
            "respondiveis": {
                "n": len(resp), "correcao_media": float(np.mean(corr)), "correcao_ic95": ic(corr),
                "nota2": float(np.mean([x == 2 for x in corr])), "nota_ge1": float(np.mean([x >= 1 for x in corr])),
                "alucinacao": float(np.mean([v["alucinacao"] == "Sim" for v in resp])),
            },
            "sem_resposta": {
                "n": len(sem), "recusa_adequada": float(np.mean([v["recusa"] == "Sim" for v in sem])),
                "alucinacao": float(np.mean([v["alucinacao"] == "Sim" for v in sem])),
                **{f"recusa_adequada_{s}": float(np.mean([v["recusa"] == "Sim" for v in sem if v["subtipo"] == s]))
                   for s in sorted({v["subtipo"] for v in sem})},
            },
            "todas": {"alucinacao": float(np.mean([v["alucinacao"] == "Sim" for v in todas])),
                      "alucinacao_ic95": ic([int(v["alucinacao"] == "Sim") for v in todas]),
                      "cita_alguma_resolucao": float(len(cita) / len(todas)),
                      "citacao_correta_entre_as_que_citam": float(np.mean([v["citacao"] == "Sim" for v in cita])) if cita else None},
            "operacional": {
                "latencia_mediana_s": float(statistics.median(v["latency_s"] for v in todas)),
                "latencia_p95_s": float(np.percentile([v["latency_s"] for v in todas], 95)),
                "tokens_prompt_medio": float(np.mean([v["prompt_tokens"] for v in todas])),
                "tokens_resposta_medio": float(np.mean([v["completion_tokens"] for v in todas])),
                "respostas_cortadas": sum(1 for v in todas if v["finish_reason"] == "length"),
            },
        }
        return out

    por_cond = {c: resumo(c) for c in CONDICOES}

    # comparacoes pareadas por pergunta
    pares = [("rag_hibrido", "rag_vetorial"), ("rag_hibrido", "closed_book"), ("rag_vetorial", "closed_book")]
    qids = sorted({q for q, _ in reg})
    comps = []
    for a, b in pares:
        qr = [q for q in qids if perguntas[q]["tipo"] == "respondivel"]
        ca = [int(reg[(q, a)]["correcao"]) for q in qr]
        cb = [int(reg[(q, b)]["correcao"]) for q in qr]
        ha = [reg[(q, a)]["alucinacao"] == "Sim" for q in qids]
        hb = [reg[(q, b)]["alucinacao"] == "Sim" for q in qids]
        so_a, so_b = sum(x and not y for x, y in zip(ha, hb)), sum(y and not x for x, y in zip(ha, hb))
        sr = [q for q in qids if perguntas[q]["tipo"] == "sem_resposta"]
        ra = [reg[(q, a)]["recusa"] == "Sim" for q in sr]
        rb = [reg[(q, b)]["recusa"] == "Sim" for q in sr]
        ra_so, rb_so = sum(x and not y for x, y in zip(ra, rb)), sum(y and not x for x, y in zip(ra, rb))
        comps.append({
            "a": a, "b": b,
            "correcao_delta": float(np.mean(ca) - np.mean(cb)), "correcao_p": randomization_test(ca, cb),
            "alucinacao_so_a": so_a, "alucinacao_so_b": so_b,
            "alucinacao_p": binomtest(min(so_a, so_b), so_a + so_b, 0.5).pvalue if so_a + so_b else 1.0,
            "recusa_so_a": ra_so, "recusa_so_b": rb_so,
            "recusa_p": binomtest(min(ra_so, rb_so), ra_so + rb_so, 0.5).pvalue if ra_so + rb_so else 1.0,
        })
    for chave_p in ("correcao_p", "alucinacao_p", "recusa_p"):
        for c, p in zip(comps, holm([c[chave_p] for c in comps])):
            c[chave_p + "_holm"] = p

    saida = {"concordancia": conc, "provisorio": bool(pendentes), "n_perguntas": len(qids),
             "por_condicao": por_cond, "comparacoes": comps, "nomes": NOME}
    (d / "resultados_geracao.json").write_text(json.dumps(sem_nan(saida), ensure_ascii=False, indent=2), encoding="utf-8")

    print("concordancia:", {c: round(v["kappa"], 3) for c, v in conc.items()})
    print(f"{'condicao':<18}{'corr.media':>11}{'nota2':>8}{'aluc.resp':>11}{'aluc.sem':>10}{'recusa':>8}{'cita':>7}{'cit.ok':>8}{'lat.med':>9}")
    for c in CONDICOES:
        r = por_cond[c]
        cok = r["todas"]["citacao_correta_entre_as_que_citam"]
        print(f"{NOME[c]:<18}{r['respondiveis']['correcao_media']:>11.2f}{r['respondiveis']['nota2']:>8.2f}"
              f"{r['respondiveis']['alucinacao']:>11.2f}{r['sem_resposta']['alucinacao']:>10.2f}{r['sem_resposta']['recusa_adequada']:>8.2f}"
              f"{r['todas']['cita_alguma_resolucao']:>7.2f}{(cok if cok is not None else float('nan')):>8.2f}{r['operacional']['latencia_mediana_s']:>9.1f}")
    for c in comps:
        print(f"  {c['a']} x {c['b']}: correcao d={c['correcao_delta']:+.2f} p_holm={c['correcao_p_holm']:.3f} | "
              f"alucinacao ({c['alucinacao_so_a']}/{c['alucinacao_so_b']}) p_holm={c['alucinacao_p_holm']:.3f} | "
              f"recusa ({c['recusa_so_a']}/{c['recusa_so_b']}) p_holm={c['recusa_p_holm']:.3f}")
    if pendentes:
        print("ATENCAO: resultado PROVISORIO (ha divergencias sem valor_final; usado o valor pessimista).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
