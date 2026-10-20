"""Reavalia os 4 metodos de recuperacao com os julgamentos de relevancia dos dois anotadores (etapa 6).

Entradas (em data/julgamentos/, ou --dir):
    julgamento_<anotador>.xlsx    planilhas preenchidas (coluna F = 0/1/2)
    pool.json                     quais metodos trouxeram cada documento (gerado por scripts/pooling.py)
    divergencias.csv              (opcional) preenchido pelos autores: coluna nota_final das divergencias

Saidas:
    divergencias.csv              notas divergentes, com a coluna nota_final para os autores decidirem
    qrels.json                    nota final de cada (consulta, documento)
    resultados_pooling.json       metricas por metodo, comparacoes pareadas e concordancia
    resultados_pooling.csv        metricas por consulta

Metricas (K = 5, documentos distintos): nDCG@5 (ganho 2^nota - 1), Precision@5, Recall@5 (em relacao aos
documentos relevantes do pool), Hit@1/3/5 e MRR, com "relevante" = nota >= 1. Testes de aleatorizacao
pareados com correcao de Holm e IC95% por bootstrap, como em scripts/evaluate.py.

Uso:
    python scripts/avaliar_julgamentos.py
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate import METHODS, bootstrap_ci, holm, randomization_test  # noqa: E402

K = 5
COMPARACOES = [("rrf", "vec"), ("rrf", "bm25"), ("vec", "bm25"), ("bm25", "fts")]


# ── leitura e concordancia ────────────────────────────────────────────────────

def ler_planilha(path: Path) -> dict[tuple[str, str], int | None]:
    """{(consulta, documento): nota}. Notas ausentes ou invalidas viram None."""
    ws = load_workbook(path, read_only=True, data_only=True)["Julgamentos"]
    notas = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        qid = str(row[0]).split("-")[0]
        v = row[5]
        notas[(qid, str(row[2]))] = int(v) if v in (0, 1, 2, "0", "1", "2") else None
    return notas


def sem_nan(obj):
    """Troca NaN por None (JSON valido), recursivamente; JSON.parse do Node rejeita NaN."""
    if isinstance(obj, dict):
        return {k: sem_nan(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sem_nan(v) for v in obj]
    if isinstance(obj, (float, np.floating)) and math.isnan(obj):
        return None
    return obj


def kappa(a: list[int], b: list[int], pesos: str = "nenhum", categorias: int = 3) -> float:
    """Kappa de Cohen (pesos="nenhum") ou ponderado (linear/quadratico) entre duas listas de notas."""
    if categorias < 2 or not len(a):
        return float("nan")      # com uma só categoria (ou sem dados) o kappa não é definido
    obs = np.zeros((categorias, categorias))
    for x, y in zip(a, b):
        obs[x, y] += 1
    obs /= obs.sum()
    esp = np.outer(obs.sum(axis=1), obs.sum(axis=0))
    i, j = np.indices(obs.shape)
    w = {"nenhum": lambda: (i != j).astype(float),
         "linear": lambda: np.abs(i - j) / (categorias - 1),
         "quadratico": lambda: ((i - j) / (categorias - 1)) ** 2}[pesos]()
    denom = (w * esp).sum()
    return float("nan") if denom == 0 else 1.0 - (w * obs).sum() / denom


# ── metricas ──────────────────────────────────────────────────────────────────

def metricas(ranking: list[str], notas: dict[str, int], universo: dict[str, int]) -> dict:
    """ranking: documentos em ordem; notas: nota de cada documento; universo: notas de todo o pool da consulta."""
    ganhos = [2 ** notas.get(d, 0) - 1 for d in ranking[:K]]
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(ganhos))
    ideal = sorted((2 ** n - 1 for n in universo.values()), reverse=True)[:K]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    rel = [notas.get(d, 0) >= 1 for d in ranking[:K]]
    n_rel = sum(1 for n in universo.values() if n >= 1)
    primeiro = next((i + 1 for i, r in enumerate(rel) if r), None)
    return {
        "ndcg5": dcg / idcg if idcg else 0.0,
        "p5": sum(rel) / K,
        "recall5": sum(rel) / n_rel if n_rel else 0.0,
        "hit1": int(any(rel[:1])), "hit3": int(any(rel[:3])), "hit5": int(any(rel)),
        "rr": 1.0 / primeiro if primeiro else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(ROOT / "data" / "julgamentos"))
    ap.add_argument("--anotadores", nargs="+", default=["matheus", "rafael"])
    ap.add_argument("--permitir-divergencias", action="store_true",
                    help="usa a media arredondada para baixo onde nao ha nota_final (resultado PROVISORIO)")
    args = ap.parse_args()
    d = Path(args.dir)

    pool = json.loads((d / "pool.json").read_text("utf-8"))
    planilhas = [ler_planilha(d / f"julgamento_{a}.xlsx") for a in args.anotadores]
    chaves = [(qid, doc) for qid, p in pool.items() for doc in p["docs"]]

    faltando = [f"{a}: {sum(1 for c in chaves if pl.get(c) is None)}" for a, pl in zip(args.anotadores, planilhas)]
    if any(not n.endswith(": 0") for n in faltando):
        print("RECUSADO: ha julgamentos em branco ou invalidos ->", "; ".join(faltando))
        return 1

    a, b = ([pl[c] for c in chaves] for pl in planilhas)
    concordancia = {
        "n_julgamentos": len(chaves),
        "concordancia_simples": float(np.mean([x == y for x, y in zip(a, b)])),
        "kappa_3_categorias": kappa(a, b),
        "kappa_ponderado_linear": kappa(a, b, "linear"),
        "kappa_ponderado_quadratico": kappa(a, b, "quadratico"),
        "kappa_relevante_vs_irrelevante": kappa([int(x >= 1) for x in a], [int(y >= 1) for y in b], categorias=2),
        "kappa_nota2_vs_demais": kappa([int(x == 2) for x in a], [int(y == 2) for y in b], categorias=2),
        "divergencias": sum(x != y for x, y in zip(a, b)),
    }

    # divergencias: o arquivo e gerado na primeira rodada; os autores preenchem nota_final
    div_path = d / "divergencias.csv"
    decididas: dict[tuple[str, str], int] = {}
    if div_path.exists():
        for r in csv.DictReader(open(div_path, encoding="utf-8-sig")):
            if r["nota_final"].strip() in ("0", "1", "2"):
                decididas[(r["consulta_id"], r["documento"])] = int(r["nota_final"])
    divergentes = [(c, x, y) for c, x, y in zip(chaves, a, b) if x != y]
    with open(div_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["consulta_id", "consulta", "documento", *[f"nota_{n}" for n in args.anotadores], "nota_final"])
        for (qid, doc), x, y in divergentes:
            w.writerow([qid, pool[qid]["query"], doc, x, y, decididas.get((qid, doc), "")])
    pendentes = [c for c, _, _ in divergentes if c not in decididas]
    if pendentes and not args.permitir_divergencias:
        print(f"{len(divergentes)} divergencias (kappa ponderado {concordancia['kappa_ponderado_quadratico']:.3f}); "
              f"{len(pendentes)} sem decisao. Preencham a coluna nota_final em {div_path} e rodem de novo "
              "(ou use --permitir-divergencias para um resultado provisorio).")
        return 2

    qrels: dict[str, dict[str, int]] = {}
    for c, x, y in zip(chaves, a, b):
        qrels.setdefault(c[0], {})[c[1]] = decididas.get(c, x if x == y else min(x, y))
    (d / "qrels.json").write_text(json.dumps(qrels, ensure_ascii=False, indent=1), encoding="utf-8")

    # metricas por consulta e metodo
    linhas = []
    for qid, p in pool.items():
        row = {"id": qid, "tipo": p["type"], "n_relevantes_pool": sum(1 for n in qrels[qid].values() if n >= 1)}
        row["referencia_antiga_nota"] = max((qrels[qid].get(r, 0) for r in p["referencia_atual"]), default=None) \
            if p["referencia_atual"] else None
        for m in METHODS:
            ranking = [doc for doc, pos in sorted(((doc, mp[m]) for doc, mp in p["docs"].items() if m in mp), key=lambda t: t[1])]
            for k, v in metricas(ranking, qrels[qid], qrels[qid]).items():
                row[f"{m}_{k}"] = v
        linhas.append(row)

    def agg(sub: list[dict], m: str) -> dict:
        out = {k: float(np.mean([r[f"{m}_{k}"] for r in sub])) for k in ("ndcg5", "p5", "recall5", "hit1", "hit3", "hit5", "rr")}
        out["ndcg5_ic95"] = list(bootstrap_ci([r[f"{m}_ndcg5"] for r in sub]))
        out["mrr"] = out.pop("rr")
        return out

    def comparar(sub: list[dict]) -> list[dict]:
        comps = []
        for x, y in COMPARACOES:
            ra, rb = [r[f"{x}_ndcg5"] for r in sub], [r[f"{y}_ndcg5"] for r in sub]
            comps.append({"a": x, "b": y, "delta_ndcg5": float(np.mean(ra) - np.mean(rb)),
                          "p": randomization_test(ra, rb),
                          "vitorias_a": sum(u > v for u, v in zip(ra, rb)), "vitorias_b": sum(u < v for u, v in zip(ra, rb)),
                          "empates": sum(u == v for u, v in zip(ra, rb))})
        for c, p in zip(comps, holm([c["p"] for c in comps])):
            c["p_holm"] = p
        return comps

    tipos = sorted({r["tipo"] for r in linhas})
    resumo = {
        "concordancia": concordancia,
        "provisorio": bool(pendentes),
        "n_consultas": len(linhas),
        "global": {m: agg(linhas, m) for m in METHODS},
        "comparacoes": comparar(linhas),
        "por_tipo": {t: {"n": sum(1 for r in linhas if r["tipo"] == t),
                         **{m: agg([r for r in linhas if r["tipo"] == t], m) for m in METHODS},
                         "comparacoes": comparar([r for r in linhas if r["tipo"] == t])} for t in tipos},
        "referencia_antiga": {
            "julgada_relevante_>=1": float(np.mean([r["referencia_antiga_nota"] >= 1 for r in linhas if r["referencia_antiga_nota"] is not None])),
            "julgada_nota_2": float(np.mean([r["referencia_antiga_nota"] == 2 for r in linhas if r["referencia_antiga_nota"] is not None])),
        },
    }
    (d / "resultados_pooling.json").write_text(json.dumps(sem_nan(resumo), ensure_ascii=False, indent=2), encoding="utf-8")
    with open(d / "resultados_pooling.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    print(f"concordancia: simples {concordancia['concordancia_simples']:.3f}, kappa ponderado (quad.) "
          f"{concordancia['kappa_ponderado_quadratico']:.3f}, kappa relevante x irrelevante {concordancia['kappa_relevante_vs_irrelevante']:.3f}")
    print(f"{'metodo':<6}" + "".join(f"{k:>10}" for k in ("nDCG@5", "P@5", "Recall@5", "Hit@1", "Hit@5", "MRR")))
    for m in METHODS:
        g = resumo["global"][m]
        print(f"{m:<6}" + "".join(f"{g[k]:>10.3f}" for k in ("ndcg5", "p5", "recall5", "hit1", "hit5", "mrr")))
    for c in resumo["comparacoes"]:
        print(f"  {c['a']:>4} x {c['b']:<4} dnDCG={c['delta_ndcg5']:+.3f}  p={c['p']:.4f}  p_holm={c['p_holm']:.4f}")
    if resumo["provisorio"]:
        print("ATENCAO: resultado PROVISORIO (ha divergencias sem nota_final).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
