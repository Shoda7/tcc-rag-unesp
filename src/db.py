"""Camada de acesso ao PostgreSQL + pgvector.

Cria o esquema (extensao vector, tabela de chunks com coluna vetorial e
indice) e oferece funcoes para inserir e consultar embeddings.
"""
from __future__ import annotations

import json

import psycopg
from pgvector.psycopg import register_vector

from . import config
from .chunk import Chunk


def connect():
    """Abre conexao com o banco e registra o tipo `vector`."""
    conn = psycopg.connect(**config.DB)
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    conn.commit()
    register_vector(conn)
    return conn


def init_schema(conn, dim: int | None = None) -> None:
    """Cria a tabela de chunks e os indices vetorial e FTS."""
    dim = dim or config.EMBEDDING_DIM
    with conn.cursor() as cur:
        # unaccent() nao e IMMUTABLE por padrao; wrapper necessario para
        # colunas GENERATED ALWAYS AS
        cur.execute("""
            CREATE OR REPLACE FUNCTION unaccent_immutable(text)
            RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
            $$ SELECT unaccent($1) $$
        """)
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id          BIGSERIAL PRIMARY KEY,
                source      TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content     TEXT NOT NULL,
                metadata    JSONB DEFAULT '{{}}'::jsonb,
                embedding   vector({dim}),
                content_tsv tsvector GENERATED ALWAYS AS
                    (to_tsvector('portuguese', unaccent_immutable(content))) STORED,
                UNIQUE (source, chunk_index)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS chunks_embedding_idx "
            "ON chunks USING hnsw (embedding vector_cosine_ops)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (content_tsv)"
        )
    conn.commit()


def rebuild_tsv(conn) -> None:
    """Recria content_tsv com unaccent (migracao de schema existente).

    unaccent() nao e IMMUTABLE por padrao no PostgreSQL, o que e exigido em
    colunas GENERATED ALWAYS AS. A solucao padrao e criar uma funcao wrapper
    marcada como IMMUTABLE que delega para unaccent().
    """
    with conn.cursor() as cur:
        # Wrapper imutavel necessario para uso em coluna gerada
        cur.execute("""
            CREATE OR REPLACE FUNCTION unaccent_immutable(text)
            RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
            $$ SELECT unaccent($1) $$
        """)
        cur.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS content_tsv")
        cur.execute("DROP INDEX IF EXISTS chunks_tsv_idx")
        cur.execute("""
            ALTER TABLE chunks ADD COLUMN content_tsv tsvector
            GENERATED ALWAYS AS
                (to_tsvector('portuguese', unaccent_immutable(content))) STORED
        """)
        cur.execute("CREATE INDEX chunks_tsv_idx ON chunks USING gin (content_tsv)")
    conn.commit()
    print("content_tsv recriada com unaccent_immutable.")


def insert_chunks(conn, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
    """Insere chunks + embeddings. Ignora duplicatas (source, chunk_index)."""
    if len(chunks) != len(embeddings):
        raise ValueError("Numero de chunks e de embeddings nao coincide.")

    inserted = 0
    with conn.cursor() as cur:
        for ck, emb in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO chunks (source, chunk_index, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source, chunk_index) DO NOTHING
                """,
                (ck.source, ck.index, ck.text, json.dumps(ck.metadata), emb),
            )
            inserted += cur.rowcount
    conn.commit()
    return inserted


def count_chunks(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM chunks")
        return cur.fetchone()[0]


def search_fts(conn, query: str, k: int = 5) -> list[dict]:
    """Baseline Full-Text Search com BM25 (ts_rank_cd) e unaccent na query."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source, chunk_index, content,
                   ts_rank_cd(content_tsv,
                       plainto_tsquery('portuguese', unaccent(%s))) AS rank
            FROM chunks
            WHERE content_tsv @@ plainto_tsquery('portuguese', unaccent(%s))
            ORDER BY rank DESC
            LIMIT %s
            """,
            (query, query, k),
        )
        rows = cur.fetchall()
    return [
        {"source": r[0], "chunk_index": r[1], "content": r[2], "rank": float(r[3])}
        for r in rows
    ]


def search_hybrid(
    conn,
    query_embedding: list[float],
    query_text: str,
    k: int = 5,
    rrf_k: int = 60,
    fetch: int = 50,
) -> list[dict]:
    """Busca híbrida via Reciprocal Rank Fusion (RRF).

    Combina os rankings da busca vetorial e da FTS usando a fórmula:
        RRF(d) = 1/(rrf_k + rank_vec) + 1/(rrf_k + rank_fts)
    rrf_k=60 é o valor padrão da literatura (Cormack et al., 2009).
    fetch controla quantos candidatos cada método retorna antes da fusão.
    """
    vec_results = search_vector(conn, query_embedding, k=fetch)
    fts_results = search_fts(conn, query_text, k=fetch)

    scores: dict[tuple, float] = {}
    content_map: dict[tuple, dict] = {}

    for rank, r in enumerate(vec_results, 1):
        key = (r["source"], r["chunk_index"])
        scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
        content_map[key] = r

    for rank, r in enumerate(fts_results, 1):
        key = (r["source"], r["chunk_index"])
        scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
        if key not in content_map:
            content_map[key] = r

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [
        {**content_map[key], "rrf_score": score}
        for key, score in ranked
    ]


def search_vector(conn, query_embedding: list[float], k: int = 5) -> list[dict]:
    """Recuperacao vetorial: retorna os k chunks mais similares (cosseno)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source, chunk_index, content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, k),
        )
        rows = cur.fetchall()
    return [
        {"source": r[0], "chunk_index": r[1], "content": r[2], "similarity": float(r[3])}
        for r in rows
    ]
