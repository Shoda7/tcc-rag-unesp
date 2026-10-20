"""Avaliação experimental da recuperação: vetorial × FTS × BM25 × híbrido RRF.

Para cada consulta de data/eval_set.json, roda os quatro métodos, deduplica o
ranking por documento (top-K documentos distintos) e calcula Hit@1/3/5, MRR e
latência. Depois compara os métodos par a par com teste de aleatorização
pareado (com correção de Holm) e estima IC 95% do MRR por bootstrap
(Smucker; Allan; Carterette, 2007).

Saídas:
    --csv   resultados por consulta
    --json  resumo agregado (lido por scripts/gerar_tcc.mjs para montar as tabelas)

Uso:
    python scripts/evaluate.py
    python scripts/evaluate.py --csv data/resultados_avaliacao.csv --json data/resultados_resumo.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config, db  # noqa: E402
from src import bm25  # noqa: E402
from src.embeddings import embed_query  # noqa: E402

METHODS = {
    "vec":  "Vetorial",
    "fts":  "FTS PostgreSQL (ts_rank_cd)",
    "bm25": "BM25",
    "rrf":  "Híbrido RRF (vetorial + BM25)",
}
USES_EMBEDDING = {"vec", "rrf"}
COMPARISONS = [("rrf", "vec"), ("rrf", "bm25"), ("vec", "bm25"), ("bm25", "fts")]
FETCH = 50      # chunks recuperados por método antes de deduplicar por documento
RRF_K = 60
N_RESAMPLES = 10_000
SEED = 42


# ── métricas ──────────────────────────────────────────────────────────────────

def top_documents(results: list[dict], k: int) -> list[str]:
    """Primeiros k documentos distintos do ranking de chunks."""
    seen: set[str] = set()
    docs: list[str] = []
    for r in results:
        if r["source"] not in seen:
            seen.add(r["source"])
            docs.append(r["source"])
            if len(docs) == k:
                break
    return docs


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, src in enumerate(retrieved, 1):
        if src in relevant:
            return 1.0 / rank
    return 0.0


def hit_at_k(retrieved: list[str], relevant: set[str], k: int) -> int:
    return int(bool(relevant.intersection(retrieved[:k])))


# ── estatística ───────────────────────────────────────────────────────────────

def randomization_test(a: list[float], b: list[float]) -> float:
    """Teste de aleatorização pareado (bicaudal) sobre a diferença de médias."""
    d = np.asarray(a, float) - np.asarray(b, float)
    if not d.any():
        return 1.0
    rng = np.random.default_rng(SEED)
    signs = rng.choice([-1.0, 1.0], size=(N_RESAMPLES, d.size))
    perm = np.abs((signs * d).mean(axis=1))
    return float((np.sum(perm >= abs(d.mean()) - 1e-12) + 1) / (N_RESAMPLES + 1))


def bootstrap_ci(x: list[float]) -> tuple[float, float]:
    """IC 95% da média por bootstrap percentil."""
    arr = np.asarray(x, float)
    rng = np.random.default_rng(SEED)
    means = arr[rng.integers(0, arr.size, size=(N_RESAMPLES, arr.size))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def holm(pvals: list[float]) -> list[float]:
    """Correção de Holm-Bonferroni para comparações múltiplas."""
    m = len(pvals)
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(sorted(range(m), key=lambda i: pvals[i])):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adjusted[i] = running
    return adjusted


# ── execução ──────────────────────────────────────────────────────────────────

def retrieve(conn, method: str, query: str, qvec: list[float]) -> list[dict]:
    if method == "vec":
        return db.search_vector(conn, qvec, k=FETCH)
    if method == "fts":
        return db.search_fts(conn, query, k=FETCH)
    if method == "bm25":
        return db.search_bm25(conn, query, k=FETCH)
    return db.search_hybrid(conn, qvec, query, k=FETCH, rrf_k=RRF_K, fetch=FETCH)


def run(eval_path: Path, k: int = 5, dbname: str | None = None) -> list[dict]:
    questions = json.loads(eval_path.read_text("utf-8"))
    conn = db.connect(dbname)

    # Aquecimento: carrega o modelo de embeddings e o índice BM25 antes de medir,
    # para que a latência da primeira consulta não inclua inicialização.
    warm = embed_query("aquecimento")
    for m in METHODS:
        retrieve(conn, m, "aquecimento", warm)

    rows = []
    for q in questions:
        relevant = set(q["relevant_sources"])
        row = {"id": q["id"], "query": q["query"], "type": q.get("type", "unknown")}

        t0 = time.perf_counter()
        qvec = embed_query(q["query"])
        embed_ms = (time.perf_counter() - t0) * 1000
        row["embed_ms"] = round(embed_ms, 2)

        marks = []
        for m in METHODS:
            t0 = time.perf_counter()
            results = retrieve(conn, m, q["query"], qvec)
            search_ms = (time.perf_counter() - t0) * 1000
            docs = top_documents(results, k)
            row[f"{m}_hit1"] = hit_at_k(docs, relevant, 1)
            row[f"{m}_hit3"] = hit_at_k(docs, relevant, 3)
            row[f"{m}_hit5"] = hit_at_k(docs, relevant, 5)
            row[f"{m}_rr"] = reciprocal_rank(docs, relevant)
            row[f"{m}_search_ms"] = round(search_ms, 2)
            row[f"{m}_ms"] = round(search_ms + (embed_ms if m in USES_EMBEDDING else 0), 2)
            row[f"{m}_n_docs"] = len(docs)
            row[f"{m}_top1"] = docs[0] if docs else ""
            marks.append(f"{m.upper()}:" + ("OK" if row[f"{m}_hit1"] else ("~5" if row[f"{m}_hit5"] else "--")))
        row["relevant"] = ";".join(sorted(relevant))
        rows.append(row)
        print(f"[{q['id']}] ({row['type'][:3]}) {' '.join(marks)}  {q['query'][:50]}")

    conn.close()
    return rows


def summarize(rows: list[dict], k: int) -> dict:
    def agg(subset: list[dict], m: str) -> dict:
        rr = [r[f"{m}_rr"] for r in subset]
        lo, hi = bootstrap_ci(rr)
        lat = [r[f"{m}_ms"] for r in subset]
        return {
            "hit1": float(np.mean([r[f"{m}_hit1"] for r in subset])),
            "hit3": float(np.mean([r[f"{m}_hit3"] for r in subset])),
            "hit5": float(np.mean([r[f"{m}_hit5"] for r in subset])),
            "mrr": float(np.mean(rr)),
            "mrr_ci95": [lo, hi],
            "lat_median_ms": float(np.median(lat)),
            "lat_p95_ms": float(np.percentile(lat, 95)),
            "sem_resultado": sum(1 for r in subset if r[f"{m}_n_docs"] == 0),
        }

    def compare(subset: list[dict]) -> list[dict]:
        comparisons = []
        for a, b in COMPARISONS:
            ra = [r[f"{a}_rr"] for r in subset]
            rb = [r[f"{b}_rr"] for r in subset]
            comparisons.append({
                "a": a, "b": b,
                "delta_mrr": float(np.mean(ra) - np.mean(rb)),
                "p_mrr": randomization_test(ra, rb),
                "p_hit1": randomization_test([r[f"{a}_hit1"] for r in subset],
                                             [r[f"{b}_hit1"] for r in subset]),
                "vitorias_a": sum(x > y for x, y in zip(ra, rb)),
                "vitorias_b": sum(x < y for x, y in zip(ra, rb)),
                "empates": sum(x == y for x, y in zip(ra, rb)),
            })
        for c, p in zip(comparisons, holm([c["p_mrr"] for c in comparisons])):
            c["p_mrr_holm"] = p
        return comparisons

    comparisons = compare(rows)

    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""

    by_type = {}
    for qtype in sorted({r["type"] for r in rows}):
        subset = [r for r in rows if r["type"] == qtype]
        by_type[qtype] = {"n": len(subset), **{m: agg(subset, m) for m in METHODS},
                          "comparacoes": compare(subset)}

    emb = [r["embed_ms"] for r in rows]
    return {
        "meta": {
            "data": date.today().isoformat(),
            "commit": commit,
            "n_consultas": len(rows),
            "k": k,
            "fetch_por_metodo": FETCH,
            "rrf_k": RRF_K,
            "hnsw_ef_search": db.HNSW_EF_SEARCH,
            "bm25_k1": bm25.K1,
            "bm25_b": bm25.B,
            "embedding_model": config.EMBEDDING_MODEL,
            "reamostragens": N_RESAMPLES,
            "seed": SEED,
        },
        "metodos": METHODS,
        "global": {m: agg(rows, m) for m in METHODS},
        "por_tipo": by_type,
        "embedding_ms": {"median": float(np.median(emb)), "p95": float(np.percentile(emb, 95))},
        "comparacoes": comparisons,
    }


def print_summary(s: dict) -> None:
    print(f"\n{'=' * 78}")
    print(f"{'Métrica':<14}" + "".join(f"{m.upper():>14}" for m in METHODS))
    print("-" * 78)
    for label, key in [("Hit@1", "hit1"), ("Hit@3", "hit3"), ("Hit@5", "hit5"), ("MRR", "mrr"),
                       ("Lat. med (ms)", "lat_median_ms"), ("Lat. p95 (ms)", "lat_p95_ms"),
                       ("Sem resultado", "sem_resultado")]:
        print(f"{label:<14}" + "".join(f"{s['global'][m][key]:>14.3f}" for m in METHODS))
    for qtype, sub in s["por_tipo"].items():
        print(f"\n  [{qtype.upper()} -- {sub['n']} consultas]")
        for label, key in [("Hit@1", "hit1"), ("Hit@5", "hit5"), ("MRR", "mrr")]:
            print(f"    {label:<8}" + "  ".join(f"{m.upper()}={sub[m][key]:.3f}" for m in METHODS))
        for c in sub["comparacoes"]:
            print(f"    {c['a'].upper():>4} x {c['b'].upper():<4} dMRR={c['delta_mrr']:+.3f}  "
                  f"p={c['p_mrr']:.4f}  p_holm={c['p_mrr_holm']:.4f}")
    print("\n  Comparações pareadas (MRR, teste de aleatorização, Holm):")
    for c in s["comparacoes"]:
        print(f"    {c['a'].upper():>4} x {c['b'].upper():<4} dMRR={c['delta_mrr']:+.3f}  "
              f"p={c['p_mrr']:.4f}  p_holm={c['p_mrr_holm']:.4f}  "
              f"(+{c['vitorias_a']} / -{c['vitorias_b']} / ={c['empates']})")
    print(f"\n  Embedding da consulta: mediana {s['embedding_ms']['median']:.1f} ms, "
          f"p95 {s['embedding_ms']['p95']:.1f} ms")
    print("=" * 78)


def save_csv(rows: list[dict], path: Path) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV salvo em: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avaliação: vetorial x FTS x BM25 x RRF")
    parser.add_argument("--eval", default="data/eval_set.json")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--json", default=None)
    parser.add_argument("--db", default=None, help="banco alternativo (ex.: das ablacoes); padrao: o do .env")
    args = parser.parse_args()

    rows = run(ROOT / args.eval, k=args.k, dbname=args.db)
    summary = summarize(rows, args.k)
    if args.csv:
        save_csv(rows, ROOT / args.csv)
    if args.json:
        (ROOT / args.json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
        print(f"Resumo salvo em: {ROOT / args.json}")
    print_summary(summary)
