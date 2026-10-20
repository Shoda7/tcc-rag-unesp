"""Ablacao do tamanho do chunk, em um banco separado (o indice principal nao e tocado).

Motivo: o multilingual-e5-small le no maximo 512 tokens por texto e os chunks de 350 palavras
tem mediana de ~540 tokens (66% passam do limite), entao o vetor so "enxerga" o inicio deles.
O script reindexa as resolucoes com outro tamanho de chunk num banco proprio, mede quantos
chunks ainda passam de 512 tokens e roda a mesma avaliacao (scripts/evaluate.py).

Uso:
  python scripts/ablacao_chunk.py --palavras 250 --sobreposicao 40
Saida: data/ablacoes/chunk<palavras>_resumo.json (+ _resultados.csv) e o banco tcc_rag_abl_c<palavras>.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config, db  # noqa: E402
from src.chunk import Chunk, chunk_text  # noqa: E402
from src.embeddings import embed_passages, get_model  # noqa: E402


def recriar_banco(nome: str) -> None:
    admin = psycopg.connect(**{**config.DB, "dbname": "postgres"}, autocommit=True)
    admin.execute(f"DROP DATABASE IF EXISTS {nome}")
    admin.execute(f"CREATE DATABASE {nome}")
    admin.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--palavras", type=int, required=True)
    ap.add_argument("--sobreposicao", type=int, required=True)
    args = ap.parse_args()

    nome_db = f"tcc_rag_abl_c{args.palavras}"
    saida = ROOT / "data" / "ablacoes"
    saida.mkdir(parents=True, exist_ok=True)

    chunks: list[Chunk] = []
    txts = sorted(config.DATA_LEGISLACAO.glob("resolucao_*.txt"))
    for t in txts:
        chunks.extend(chunk_text(t.read_text(encoding="utf-8"), t.name, size=args.palavras, overlap=args.sobreposicao))
    print(f"{len(chunks)} chunks de {len(txts)} documentos ({args.palavras} palavras, sobreposicao {args.sobreposicao})")

    modelo = get_model()
    limite = modelo.max_seq_length
    n_tok = [len(modelo.tokenizer(f"passage: {c.text}")["input_ids"]) for c in chunks]
    truncados = sum(1 for n in n_tok if n > limite)
    estat = {
        "palavras": args.palavras, "sobreposicao": args.sobreposicao, "chunks": len(chunks),
        "tokens_mediana": statistics.median(n_tok), "tokens_p95": sorted(n_tok)[int(0.95 * len(n_tok))],
        "limite_tokens": limite, "chunks_truncados": truncados, "pct_truncados": round(100 * truncados / len(n_tok), 1),
    }
    print(json.dumps(estat, ensure_ascii=False))

    print("Gerando embeddings...")
    vetores = embed_passages([c.text for c in chunks])
    recriar_banco(nome_db)
    conn = db.connect(nome_db)
    db.init_schema(conn, dim=modelo.get_sentence_embedding_dimension() if hasattr(modelo, "get_sentence_embedding_dimension") else config.EMBEDDING_DIM)
    db.insert_chunks(conn, chunks, vetores)
    conn.close()
    print(f"banco {nome_db} pronto; avaliando...")

    prefixo = f"data/ablacoes/chunk{args.palavras}"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "evaluate.py"), "--db", nome_db,
         "--json", f"{prefixo}_resumo.json", "--csv", f"{prefixo}_resultados.csv"],
        check=True, cwd=ROOT,
    )
    resumo = json.loads((ROOT / f"{prefixo}_resumo.json").read_text("utf-8"))
    resumo["chunking"] = estat
    (ROOT / f"{prefixo}_resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
