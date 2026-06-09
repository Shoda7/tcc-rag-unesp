"""Configuracao central do projeto, carregada de variaveis de ambiente (.env)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto (pasta que contem este arquivo /src)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Diretorios de dados
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_LEGISLACAO = ROOT / "data" / "legislacao"
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
DATA_LEGISLACAO.mkdir(parents=True, exist_ok=True)

# ----- Banco de dados -----
DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "tcc_rag"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

# ----- Embeddings -----
# Modelo efetivamente utilizado no projeto: e5-small (384 dims), executado localmente.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

# ----- Chunking -----
CHUNK_SIZE_WORDS = int(os.getenv("CHUNK_SIZE_WORDS", "350"))
CHUNK_OVERLAP_WORDS = int(os.getenv("CHUNK_OVERLAP_WORDS", "60"))

# ----- LLM (Groq) -----
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ----- Scraper -----
SCRAPER_SEEDS = [
    u.strip() for u in os.getenv("SCRAPER_SEEDS", "").split(",") if u.strip()
]
SCRAPER_MAX_DEPTH = int(os.getenv("SCRAPER_MAX_DEPTH", "2"))
SCRAPER_SAME_DOMAIN = os.getenv("SCRAPER_SAME_DOMAIN", "true").lower() == "true"
