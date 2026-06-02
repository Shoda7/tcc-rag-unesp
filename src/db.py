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
    conn.commit()
    register_vector(conn)
    return conn


def init_schema(conn, dim: int | None = None) -> None:
    """Cria a tabela de chunks e o indice vetorial (HNSW)."""
    dim = dim or config.EMBEDDING_DIM
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id          BIGSERIAL PRIMARY KEY,
                source      TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content     TEXT NOT NULL,
                metadata    JSONB DEFAULT '{{}}'::jsonb,
                embedding   vector({dim}),
                -- coluna para o baseline Full-Text Search (atividade de julho)
                content_tsv tsvector GENERATED ALWAYS AS
                    (to_tsvector('portuguese', content)) STORED,
                UNIQUE (source, chunk_index)
            )
            """
        )
        # Indice vetorial para busca por similaridade de cosseno
        cur.execute(
            "CREATE INDEX IF NOT EXISTS chunks_embedding_idx "
            "ON chunks USING hnsw (embedding vector_cosine_ops)"
        )
        # Indice GIN para o Full-Text Search (baseline comparativo)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (content_tsv)"
        )
    conn.commit()


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
