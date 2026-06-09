"""Avaliação experimental: busca vetorial vs. FTS (BM25) vs. híbrido RRF.

Carrega data/eval_set.json, roda os três métodos em cada query e calcula
Hit@1, Hit@3, Hit@5, MRR e latência para cada método e tipo de query.

Uso:
    python scripts/evaluate.py                  # resultados no terminal
    python scripts/evaluate.py --csv resultados.csv
"""
from __future__ import annotations

import argparse
import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import db          # noqa: E402
from src.embeddings import embed_query  # noqa: E402


# ── métricas ──────────────────────────────────────────────────────────────────

def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, src in enumerate(retrieved, 1):
        if src in relevant:
            return 1.0 / rank
    return 0.0


def hit_at_k(retrieved: list[str], relevant: set[str], k: int) -> int:
    return int(bool(relevant.intersection(retrieved[:k])))


def evaluate_results(retrieved: list[str], relevant: set[str]) -> dict:
    return {
        "hit@1": hit_at_k(retrieved, relevant, 1),
        "hit@3": hit_at_k(retrieved, relevant, 3),
        "hit@5": hit_at_k(retrieved, relevant, 5),
        "rr":    reciprocal_rank(retrieved, relevant),
    }


# ── execução ──────────────────────────────────────────────────────────────────

def run(eval_path: Path, k: int = 5) -> list[dict]:
    questions = json.loads(eval_path.read_text("utf-8"))
    conn = db.connect()
    rows = []

    for q in questions:
        relevant = set(q["relevant_sources"])
        qtype = q.get("type", "unknown")

        # --- embed query (shared) ---
        t0 = time.perf_counter()
        qvec = embed_query(q["query"])
        embed_ms = (time.perf_counter() - t0) * 1000

        # --- vetor ---
        t0 = time.perf_counter()
        vec_results = db.search_vector(conn, qvec, k=k)
        vec_ms = (time.perf_counter() - t0) * 1000
        vec_sources = [r["source"] for r in vec_results]
        vec_metrics = evaluate_results(vec_sources, relevant)

        # --- FTS ---
        t0 = time.perf_counter()
        fts_results = db.search_fts(conn, q["query"], k=k)
        fts_ms = (time.perf_counter() - t0) * 1000
        fts_sources = [r["source"] for r in fts_results]
        fts_metrics = evaluate_results(fts_sources, relevant)

        # --- híbrido RRF ---
        t0 = time.perf_counter()
        rrf_results = db.search_hybrid(conn, qvec, q["query"], k=k)
        rrf_ms = (time.perf_counter() - t0) * 1000
        rrf_sources = [r["source"] for r in rrf_results]
        rrf_metrics = evaluate_results(rrf_sources, relevant)

        rows.append({
            "id":        q["id"],
            "query":     q["query"][:60],
            "type":      qtype,
            # vetorial
            "vec_hit1":  vec_metrics["hit@1"],
            "vec_hit3":  vec_metrics["hit@3"],
            "vec_hit5":  vec_metrics["hit@5"],
            "vec_rr":    vec_metrics["rr"],
            "vec_ms":    round(embed_ms + vec_ms, 1),
            # FTS
            "fts_hit1":  fts_metrics["hit@1"],
            "fts_hit3":  fts_metrics["hit@3"],
            "fts_hit5":  fts_metrics["hit@5"],
            "fts_rr":    fts_metrics["rr"],
            "fts_ms":    round(fts_ms, 1),
            # híbrido RRF
            "rrf_hit1":  rrf_metrics["hit@1"],
            "rrf_hit3":  rrf_metrics["hit@3"],
            "rrf_hit5":  rrf_metrics["hit@5"],
            "rrf_rr":    rrf_metrics["rr"],
            "rrf_ms":    round(embed_ms + rrf_ms, 1),
            # top-1 de cada
            "vec_top1":  vec_sources[0] if vec_sources else "",
            "fts_top1":  fts_sources[0] if fts_sources else "",
            "rrf_top1":  rrf_sources[0] if rrf_sources else "",
            "relevant":  list(relevant)[0],
        })

        mv = "OK" if vec_metrics["hit@1"] else ("~5" if vec_metrics["hit@5"] else "--")
        mf = "OK" if fts_metrics["hit@1"] else ("~5" if fts_metrics["hit@5"] else "--")
        mr = "OK" if rrf_metrics["hit@1"] else ("~5" if rrf_metrics["hit@5"] else "--")
        print(f"[{q['id']}] ({qtype[:3]}) VEC:{mv} FTS:{mf} RRF:{mr}  {q['query'][:50]}")

    conn.close()

    # ── resumo agregado ───────────────────────────────────────────────────────
    def mean(vals): return sum(vals) / len(vals) if vals else 0.0

    print(f"\n{'='*70}")
    print(f"{'Metrica':<10}  {'Vetorial':>10}  {'FTS (BM25)':>10}  {'Hibrido RRF':>12}")
    print(f"{'-'*70}")
    for label, vk, fk, rk in [
        ("Hit@1",  "vec_hit1", "fts_hit1", "rrf_hit1"),
        ("Hit@3",  "vec_hit3", "fts_hit3", "rrf_hit3"),
        ("Hit@5",  "vec_hit5", "fts_hit5", "rrf_hit5"),
        ("MRR",    "vec_rr",   "fts_rr",   "rrf_rr"),
        ("Lat(ms)","vec_ms",   "fts_ms",   "rrf_ms"),
    ]:
        v = mean([r[vk] for r in rows])
        f = mean([r[fk] for r in rows])
        h = mean([r[rk] for r in rows])
        best = max(v, f, h)
        winner = ("VEC" if v == best else ("FTS" if f == best else "RRF"))
        print(f"{label:<10}  {v:>10.3f}  {f:>10.3f}  {h:>12.3f}  <- {winner}")

    for qtype in ("lexical", "semantic"):
        subset = [r for r in rows if r["type"] == qtype]
        if not subset:
            continue
        print(f"\n  [{qtype.upper()} -- {len(subset)} queries]")
        for label, vk, fk, rk in [
            ("Hit@1", "vec_hit1", "fts_hit1", "rrf_hit1"),
            ("MRR",   "vec_rr",   "fts_rr",   "rrf_rr"),
        ]:
            v = mean([r[vk] for r in subset])
            f = mean([r[fk] for r in subset])
            h = mean([r[rk] for r in subset])
            print(f"    {label:<8}  VEC={v:.3f}  FTS={f:.3f}  RRF={h:.3f}")

    print(f"{'='*70}")
    return rows


def save_csv(rows: list[dict], path: Path) -> None:
    import csv
    fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV salvo em: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avaliacao vetorial vs FTS vs RRF")
    parser.add_argument("--eval", default="data/eval_set.json")
    parser.add_argument("--k",    type=int, default=5)
    parser.add_argument("--csv",  default=None)
    args = parser.parse_args()

    rows = run(ROOT / args.eval, k=args.k)
    if args.csv:
        save_csv(rows, ROOT / args.csv)
