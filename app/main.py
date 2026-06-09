"""Backend FastAPI para o sistema RAG de consulta de documentos da UNESP.

Endpoints:
    POST /api/ask     — consulta RAG completa (embed → híbrido RRF → LLM)
    POST /api/search  — apenas recuperação (sem LLM), retorna chunks ranqueados
    GET  /api/health  — verifica se o banco e o modelo estão disponíveis

Uso:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# garante que src/ é importável ao rodar de qualquer diretório
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import db, llm          # noqa: E402
from src.embeddings import embed_query  # noqa: E402

app = FastAPI(
    title="RAG UNESP Bauru",
    description="Sistema de consulta de documentos regulatórios via RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# conexão lazy — criada na primeira requisição
_conn = None


def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        _conn = db.connect()
    return _conn


# ── schemas ───────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    k: int = Field(5, ge=1, le=20)
    method: Literal["hybrid", "vector", "fts"] = "hybrid"


class SourceChunk(BaseModel):
    source: str
    chunk_index: int
    content: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    latency_ms: float


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    k: int = Field(5, ge=1, le=20)
    method: Literal["hybrid", "vector", "fts"] = "hybrid"


class SearchResponse(BaseModel):
    results: list[SourceChunk]
    latency_ms: float


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    t0 = time.perf_counter()
    try:
        conn = get_conn()
        chunks = _retrieve(conn, req.query, req.k, req.method)
        if not chunks:
            raise HTTPException(status_code=404, detail="Nenhum trecho relevante encontrado.")
        answer = llm.ask(req.query, chunks)
        latency = (time.perf_counter() - t0) * 1000
        return AskResponse(
            answer=answer,
            sources=[_to_source(c) for c in chunks],
            latency_ms=round(latency, 1),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest):
    t0 = time.perf_counter()
    try:
        conn = get_conn()
        chunks = _retrieve(conn, req.query, req.k, req.method)
        latency = (time.perf_counter() - t0) * 1000
        return SearchResponse(
            results=[_to_source(c) for c in chunks],
            latency_ms=round(latency, 1),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/health")
def health():
    try:
        conn = get_conn()
        n = db.count_chunks(conn)
        return {"status": "ok", "chunks_indexed": n}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


# ── helpers ───────────────────────────────────────────────────────────────────

def _retrieve(conn, query: str, k: int, method: str) -> list[dict]:
    qvec = embed_query(query)
    if method == "hybrid":
        return db.search_hybrid(conn, qvec, query, k=k)
    if method == "vector":
        return db.search_vector(conn, qvec, k=k)
    return db.search_fts(conn, query, k=k)


def _to_source(chunk: dict) -> SourceChunk:
    score = chunk.get("rrf_score") or chunk.get("similarity") or chunk.get("rank") or 0.0
    return SourceChunk(
        source=chunk["source"],
        chunk_index=chunk["chunk_index"],
        content=chunk["content"],
        score=round(float(score), 5),
    )
