"""Geracao de embeddings com modelo local open-source (sentence-transformers).

Por padrao usa o intfloat/multilingual-e5-large. Os modelos da familia E5
exigem prefixos: "passage: " para documentos indexados e "query: " para
consultas. Esta classe cuida disso automaticamente.
"""
from __future__ import annotations

from . import config

_model = None  # carregado sob demanda (lazy) para nao pesar a importacao


def _is_e5(model_name: str) -> bool:
    return "e5" in model_name.lower()


def get_model():
    """Carrega o modelo de embeddings uma unica vez (singleton)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Carregando modelo de embeddings: {config.EMBEDDING_MODEL} ...")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        # get_embedding_dimension() e o nome atual; get_sentence_embedding_dimension()
        # foi renomeado em sentence-transformers >= 4.x
        get_dim = getattr(_model, "get_embedding_dimension", None) or \
                  getattr(_model, "get_sentence_embedding_dimension")
        dim = get_dim()
        if dim != config.EMBEDDING_DIM:
            print(
                f"[aviso] EMBEDDING_DIM={config.EMBEDDING_DIM} no .env, mas o modelo "
                f"produz {dim} dimensoes. Ajuste o .env para {dim}."
            )
    return _model


def embed_passages(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    """Gera embeddings normalizados para textos de documentos (para indexar)."""
    model = get_model()
    if _is_e5(config.EMBEDDING_MODEL):
        texts = [f"passage: {t}" for t in texts]
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,  # permite usar similaridade por produto interno/cosseno
        show_progress_bar=True,
    )
    return vecs.tolist()


def embed_query(text: str) -> list[float]:
    """Gera o embedding de uma consulta (usado na fase de recuperacao)."""
    model = get_model()
    if _is_e5(config.EMBEDDING_MODEL):
        text = f"query: {text}"
    vec = model.encode([text], normalize_embeddings=True)[0]
    return vec.tolist()
