"""Avaliação experimental: busca vetorial vs. FTS (BM25).

Carrega data/eval_set.json, roda os dois métodos em cada query e calcula
Hit@1, Hit@3, Hit@5 e MRR para cada método e tipo de query (lexical / semantic).

Uso:
    python scripts/evaluate.py                  # resultados no terminal
    python scripts/evaluate.py --csv resultados.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Garante que src/ é importável
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import db  # noqa: E402
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

def run(eval_path: Path, k: int = 5) -> None:
    questions = json.loads(eval_path.read_text("utf-8"))

    conn = db.connect()

    rows = []
    for q in questions:
        relevant = set(q["relevant_sources"])
        qtype = q.get("type", "unknown")

        # --- vetor ---
        vec = embed_query(q["query"])
        vec_results = db.search_vector(conn, vec, k=k)
        vec_sources = [r["source"] for r in vec_results]
        vec_metrics = evaluate_results(vec_sources, relevant)

        # --- FTS ---
        fts_results = db.search_fts(conn, q["query"], k=k)
        fts_sources = [r["source"] for r in fts_results]
        fts_metrics = evaluate_results(fts_sources, relevant)

        rows.append({
            "id": q["id"],
            "query": q["query"][:60],
            "type": qtype,
            "vec_hit1": vec_metrics["hit@1"],
            "vec_hit3": vec_metrics["hit@3"],
            "vec_hit5": vec_metrics["hit@5"],
            "vec_rr":   vec_metrics["rr"],
            "fts_hit1": fts_metrics["hit@1"],
            "fts_hit3": fts_metrics["hit@3"],
            "fts_hit5": fts_metrics["hit@5"],
            "fts_rr":   fts_metrics["rr"],
            "vec_top1": vec_sources[0] if vec_sources else "",
            "fts_top1": fts_sources[0] if fts_sources else "",
            "relevant": list(relevant)[0],
        })

        mark_v = "OK" if vec_metrics["hit@1"] else ("~5" if vec_metrics["hit@5"] else "--")
        mark_f = "OK" if fts_metrics["hit@1"] else ("~5" if fts_metrics["hit@5"] else "--")
        print(f"[{q['id']}] ({qtype[:3]}) VEC:{mark_v}  FTS:{mark_f}  — {q['query'][:55]}")

    conn.close()

    # ── resumo agregado ───────────────────────────────────────────────────────
    def mean(vals):
        return sum(vals) / len(vals) if vals else 0.0

    n = len(rows)
    print(f"\n{'='*62}")
    print(f"{'Métrica':<12}  {'Vetorial':>10}  {'FTS (BM25)':>10}")
    print(f"{'-'*62}")
    for metric, vk, fk in [
        ("Hit@1",  "vec_hit1", "fts_hit1"),
        ("Hit@3",  "vec_hit3", "fts_hit3"),
        ("Hit@5",  "vec_hit5", "fts_hit5"),
        ("MRR",    "vec_rr",   "fts_rr"),
    ]:
        v = mean([r[vk] for r in rows])
        f = mean([r[fk] for r in rows])
        winner = "<-- VEC" if v > f else ("<-- FTS" if f > v else "empate")
        print(f"{metric:<12}  {v:>10.3f}  {f:>10.3f}  {winner}")

    # por tipo
    for qtype in ("lexical", "semantic"):
        subset = [r for r in rows if r["type"] == qtype]
        if not subset:
            continue
        print(f"\n  [{qtype.upper()} — {len(subset)} queries]")
        for metric, vk, fk in [("Hit@1","vec_hit1","fts_hit1"),("MRR","vec_rr","fts_rr")]:
            v = mean([r[vk] for r in subset])
            f = mean([r[fk] for r in subset])
            print(f"    {metric:<8}  VEC={v:.3f}  FTS={f:.3f}")
    print(f"{'='*62}")

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
    parser = argparse.ArgumentParser(description="Avaliação vetorial vs FTS")
    parser.add_argument("--eval", default="data/eval_set.json", help="Conjunto de avaliação")
    parser.add_argument("--k",    type=int, default=5,           help="Top-K a recuperar")
    parser.add_argument("--csv",  default=None,                  help="Salvar resultados em CSV")
    args = parser.parse_args()

    eval_path = ROOT / args.eval
    rows = run(eval_path, k=args.k)

    if args.csv:
        save_csv(rows, ROOT / args.csv)
