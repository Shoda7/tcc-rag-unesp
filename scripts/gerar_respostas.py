"""Gera as respostas do experimento de geracao em 3 condicoes.

    closed_book    : o LLM responde sem nenhum trecho (conhecimento proprio)
    rag_vetorial   : RAG com os 5 trechos mais proximos (busca vetorial)
    rag_hibrido    : RAG com os 5 trechos do hibrido RRF (vetorial + BM25)

Cada resposta e gravada em data/geracao/respostas.jsonl assim que termina. O script e RESUMIVEL: pares
(pergunta, condicao) ja gravados sao pulados, entao pode ser interrompido e rodado de novo (inclusive em
outro dia, se o limite diario do plano gratuito do Groq acabar).

Espacamento: o plano gratuito limita a 8.000 tokens/minuto; depois de cada chamada o script espera o tempo
necessario para ficar abaixo de ~80% desse limite.

Uso:
    python scripts/gerar_respostas.py            # tudo
    python scripts/gerar_respostas.py --limite 3 # so as 3 primeiras perguntas (teste)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config, db, llm  # noqa: E402
from src.embeddings import embed_query  # noqa: E402

PERGUNTAS = ROOT / "data" / "geracao" / "perguntas.json"
SAIDA = ROOT / "data" / "geracao" / "respostas.jsonl"
CONDICOES = ["closed_book", "rag_vetorial", "rag_hibrido"]
K = 5
TPM_ALVO = 8000 * 0.8          # tokens por minuto que aceitamos usar


def feitas() -> set[tuple[str, str]]:
    if not SAIDA.exists():
        return set()
    return {(r["id"], r["condicao"]) for r in map(json.loads, SAIDA.read_text("utf-8").splitlines()) if r.get("answer") is not None}


def recuperar(conn, condicao: str, pergunta: str) -> list[dict] | None:
    if condicao == "closed_book":
        return None
    qvec = embed_query(pergunta)
    if condicao == "rag_vetorial":
        return db.search_vector(conn, qvec, k=K)
    return db.search_hybrid(conn, qvec, pergunta, k=K)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limite", type=int, default=None, help="processa so as N primeiras perguntas")
    args = ap.parse_args()

    perguntas = json.loads(PERGUNTAS.read_text("utf-8"))[: args.limite]
    ja = feitas()
    pendentes = [(q, c) for q in perguntas for c in CONDICOES if (q["id"], c) not in ja]
    print(f"modelo: {config.GROQ_MODEL}   perguntas: {len(perguntas)}   pendentes: {len(pendentes)} de {len(perguntas) * len(CONDICOES)}")
    if not pendentes:
        return 0

    conn = db.connect()
    embed_query("aquecimento")
    t_inicio = time.time()
    for n, (q, condicao) in enumerate(pendentes, 1):
        chunks = recuperar(conn, condicao, q["pergunta"])
        t0 = time.perf_counter()
        try:
            r = llm.generate(q["pergunta"], chunks)
        except Exception as exc:  # noqa: BLE001  (limite diario, rede...) -> para sem perder o que ja foi gravado
            print(f"\nPARADO em {q['id']}/{condicao}: {type(exc).__name__}: {str(exc)[:200]}")
            print("Rode o script de novo mais tarde: ele continua de onde parou.")
            return 2
        total_s = time.perf_counter() - t0
        registro = {
            "id": q["id"], "condicao": condicao, "pergunta": q["pergunta"], "tipo": q["tipo"],
            "fontes_recuperadas": [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in (chunks or [])],
            "contexto_caracteres": sum(len(c["content"]) for c in (chunks or [])),
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
            **r,
        }
        with open(SAIDA, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        aviso = "  [CORTADA: finish_reason=length]" if r["finish_reason"] == "length" else ""
        print(f"[{n}/{len(pendentes)}] {q['id']} {condicao:<12} {r['prompt_tokens']}+{r['completion_tokens']} tok  "
              f"{r['latency_s']:.1f}s{aviso}", flush=True)
        # espaca as chamadas para ficar abaixo do limite de tokens por minuto
        espera = (r["prompt_tokens"] + r["completion_tokens"]) / (TPM_ALVO / 60) - total_s
        if n < len(pendentes) and espera > 0:
            time.sleep(espera)
    conn.close()
    print(f"\nconcluido em {(time.time() - t_inicio) / 60:.1f} min -> {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
