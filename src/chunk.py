"""Segmentacao do texto em chunks com janela deslizante (sliding window).

Estrategia recomendada pela literatura (Gao et al., 2023) para preservar
contexto entre segmentos: janelas de tamanho fixo (em palavras) com
sobreposicao entre chunks consecutivos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class Chunk:
    source: str          # nome do documento de origem
    index: int           # posicao do chunk dentro do documento
    text: str
    metadata: dict = field(default_factory=dict)


def chunk_text(
    text: str,
    source: str,
    size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """Divide um texto em chunks de `size` palavras com `overlap` de sobreposicao."""
    size = size or config.CHUNK_SIZE_WORDS
    overlap = overlap if overlap is not None else config.CHUNK_OVERLAP_WORDS
    if overlap >= size:
        raise ValueError("overlap deve ser menor que size.")

    words = text.split()
    chunks: list[Chunk] = []
    step = size - overlap
    idx = 0
    for start in range(0, len(words), step):
        window = words[start:start + size]
        if not window:
            break
        chunk_str = " ".join(window)
        chunks.append(
            Chunk(
                source=source,
                index=idx,
                text=chunk_str,
                metadata={
                    "word_start": start,
                    "word_end": start + len(window),
                    "n_words": len(window),
                },
            )
        )
        idx += 1
        if start + size >= len(words):
            break
    return chunks


def chunk_all() -> list[Chunk]:
    """Gera chunks para todos os .txt em data/processed."""
    txts = sorted(config.DATA_PROCESSED.glob("*.txt"))
    if not txts:
        print(f"Nenhum .txt encontrado em {config.DATA_PROCESSED}. Rode a extracao primeiro.")
        return []

    all_chunks: list[Chunk] = []
    for txt in txts:
        text = txt.read_text(encoding="utf-8")
        cks = chunk_text(text, source=txt.name)
        all_chunks.extend(cks)
        print(f"{txt.name}: {len(cks)} chunks")

    print(f"\nTotal: {len(all_chunks)} chunks de {len(txts)} documentos.")
    return all_chunks


if __name__ == "__main__":
    chunk_all()
