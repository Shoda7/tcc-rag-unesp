"""Smoke test do banco: valida esquema, insercao e busca vetorial usando
vetores sinteticos (nao baixa o modelo de embeddings).

Roda em um banco separado (tcc_rag_smoke), para nunca tocar no indice real.

Uso: python -m tests.smoke_db
"""
from __future__ import annotations

import psycopg

from src import config, db
from src.chunk import Chunk

DIM = 4  # dimensao pequena so para o teste
SMOKE_DB = "tcc_rag_smoke"


def _ensure_smoke_db() -> None:
    admin = psycopg.connect(**{**config.DB, "dbname": "postgres"}, autocommit=True)
    exists = admin.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s", (SMOKE_DB,)
    ).fetchone()
    if not exists:
        admin.execute(f"CREATE DATABASE {SMOKE_DB}")
    admin.close()


def main() -> None:
    _ensure_smoke_db()
    conn = db.connect(dbname=SMOKE_DB)
    # Recria a tabela com dimensao pequena para o teste
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS chunks")
    conn.commit()
    db.init_schema(conn, dim=DIM)

    chunks = [
        Chunk(source="doc_teste.txt", index=0, text="prazo de entrega do TCC e o ultimo dia do semestre"),
        Chunk(source="doc_teste.txt", index=1, text="o regimento trata de matricula e trancamento"),
    ]
    embeddings = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ]
    inserted = db.insert_chunks(conn, chunks, embeddings)
    assert inserted == 2, f"esperava 2 inseridos, obtive {inserted}"

    # Idempotencia: reinserir nao duplica
    again = db.insert_chunks(conn, chunks, embeddings)
    assert again == 0, f"insercao duplicada deveria ser 0, obtive {again}"

    # Busca: consulta proxima do primeiro vetor
    results = db.search_vector(conn, [0.9, 0.1, 0.0, 0.0], k=2)
    assert results[0]["chunk_index"] == 0, "o chunk mais similar deveria ser o 0"
    assert results[0]["similarity"] > results[1]["similarity"]

    print("total de chunks:", db.count_chunks(conn))
    print("top-1:", results[0]["source"], results[0]["chunk_index"],
          f"sim={results[0]['similarity']:.3f}")

    # Limpa a tabela de teste
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS chunks")
    conn.commit()
    conn.close()
    print("\nSMOKE TEST OK: esquema, insercao, idempotencia e busca vetorial validados.")


if __name__ == "__main__":
    main()
