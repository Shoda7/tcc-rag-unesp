"""Compara a ablacao do tamanho do chunk com a configuracao principal (350 palavras, sobreposicao 60).

Para cada metodo, compara o reciproco da posicao por consulta nas duas configuracoes com o mesmo teste
de aleatorizacao pareado do scripts/evaluate.py, com correcao de Holm sobre os quatro metodos.
Os numeros da secao de ablacao do TCC vem do JSON gerado aqui.

Pre-requisitos:
  python scripts/ablacao_chunk.py --palavras 350 --sobreposicao 60 --so-estatisticas
  python scripts/ablacao_chunk.py --palavras 250 --sobreposicao 40

Uso:
  python scripts/comparar_ablacao.py [--palavras 250]
Saida: data/ablacoes/comparacao_chunk<palavras>.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate import METHODS, bootstrap_ci, holm, randomization_test  # noqa: E402

BASE_CSV = ROOT / "data" / "resultados_avaliacao.csv"
ABL = ROOT / "data" / "ablacoes"


def ler_csv(caminho: Path) -> dict[str, dict]:
    with caminho.open(encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def metricas(linhas: list[dict], m: str) -> dict:
    rr = [float(r[f"{m}_rr"]) for r in linhas]
    lo, hi = bootstrap_ci(rr)
    return {
        "hit1": float(np.mean([int(r[f"{m}_hit1"]) for r in linhas])),
        "hit5": float(np.mean([int(r[f"{m}_hit5"]) for r in linhas])),
        "mrr": float(np.mean(rr)),
        "mrr_ci95": [lo, hi],
    }


def comparar(base: list[dict], abl: list[dict]) -> list[dict]:
    comps = []
    for m in METHODS:
        rb = [float(r[f"{m}_rr"]) for r in base]
        ra = [float(r[f"{m}_rr"]) for r in abl]
        comps.append({
            "metodo": m,
            "mrr_base": float(np.mean(rb)),
            "mrr_ablacao": float(np.mean(ra)),
            "delta_mrr": float(np.mean(ra) - np.mean(rb)),
            "p_mrr": randomization_test(ra, rb),
            "melhora": sum(a > b for a, b in zip(ra, rb)),
            "piora": sum(a < b for a, b in zip(ra, rb)),
            "empates": sum(a == b for a, b in zip(ra, rb)),
        })
    for c, p in zip(comps, holm([c["p_mrr"] for c in comps])):
        c["p_mrr_holm"] = p
    return comps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--palavras", type=int, default=250)
    args = ap.parse_args()

    resumo_abl = json.loads((ABL / f"chunk{args.palavras}_resumo.json").read_text("utf-8"))
    estat_base = json.loads((ABL / "chunk350_estatisticas.json").read_text("utf-8"))
    base = ler_csv(BASE_CSV)
    abl = ler_csv(ABL / f"chunk{args.palavras}_resultados.csv")
    if set(base) != set(abl):
        sys.exit(f"as consultas diferem entre as configuracoes: {sorted(set(base) ^ set(abl))}")
    ids = sorted(base)
    lb, la = [base[i] for i in ids], [abl[i] for i in ids]

    saida = {
        "base": {"chunking": estat_base, "global": {m: metricas(lb, m) for m in METHODS}},
        "ablacao": {"chunking": resumo_abl["chunking"], "global": {m: metricas(la, m) for m in METHODS},
                    "latencia_mediana_ms": {m: resumo_abl["global"][m]["lat_median_ms"] for m in METHODS}},
        "n_consultas": len(ids),
        "comparacoes": comparar(lb, la),
        "por_tipo": {},
    }
    for tipo in sorted({r["type"] for r in lb}):
        sb = [r for r in lb if r["type"] == tipo]
        sa = [r for r in la if r["type"] == tipo]
        saida["por_tipo"][tipo] = {"n": len(sb), "comparacoes": comparar(sb, sa)}

    destino = ABL / f"comparacao_chunk{args.palavras}.json"
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=2), "utf-8")

    print(f"{'metodo':6} {'MRR 350':>8} {'MRR ' + str(args.palavras):>8} {'delta':>7} {'p':>7} {'p Holm':>7}  melhora/piora/empate")
    for c in saida["comparacoes"]:
        print(f"{c['metodo']:6} {c['mrr_base']:8.3f} {c['mrr_ablacao']:8.3f} {c['delta_mrr']:+7.3f} "
              f"{c['p_mrr']:7.3f} {c['p_mrr_holm']:7.3f}  {c['melhora']}/{c['piora']}/{c['empates']}")
    for tipo, d in saida["por_tipo"].items():
        print(f"-- {tipo} ({d['n']})")
        for c in d["comparacoes"]:
            print(f"   {c['metodo']:6} {c['mrr_base']:6.3f} -> {c['mrr_ablacao']:6.3f}  p Holm {c['p_mrr_holm']:.3f}")
    print(f"gravado: {destino.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
