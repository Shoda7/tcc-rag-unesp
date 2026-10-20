"""Exporta para data/config_sistema.json os prompts e parametros do sistema que o texto do TCC cita.

Assim o documento (scripts/gerar_tcc.mjs) le os valores direto do codigo e nao diverge dele.

Uso: python scripts/exportar_config_doc.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config, llm  # noqa: E402

SAIDA = ROOT / "data" / "config_sistema.json"


def main() -> None:
    dados = {
        "prompt_rag": llm._SYSTEM,
        "prompt_sem_contexto": llm._SYSTEM_SEM_CONTEXTO,
        "modelo_llm": config.GROQ_MODEL,
        "temperatura": 0.1,
        "max_tokens": config.GROQ_MAX_TOKENS,
        "reasoning_effort": config.GROQ_REASONING_EFFORT,
        "trechos_por_pergunta": 5,
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dim": config.EMBEDDING_DIM,
        "chunk_palavras": config.CHUNK_SIZE_WORDS,
        "chunk_sobreposicao": config.CHUNK_OVERLAP_WORDS,
    }
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ok:", SAIDA)


if __name__ == "__main__":
    main()
