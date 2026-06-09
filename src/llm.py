"""Geração de respostas via Groq (componente G do pipeline RAG).

Groq expõe uma API compatível com OpenAI, então usamos o pacote `openai`
apontando para o endpoint do Groq. Modelo padrão: llama-3.3-70b-versatile.
"""
from __future__ import annotations

from . import config

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            api_key=config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


_SYSTEM = (
    "Você é um assistente especializado em documentos regulatórios da UNESP. "
    "Responda à pergunta do usuário com base exclusivamente nos trechos fornecidos. "
    "Se a informação não estiver nos trechos, diga claramente que não encontrou nos "
    "documentos disponíveis. Cite as fontes pelo nome do arquivo entre colchetes, "
    "por exemplo [resolucao_2023_0001.txt]. Responda em português."
)


def ask(query: str, chunks: list[dict], model: str | None = None) -> str:
    """Gera resposta fundamentada nos chunks recuperados.

    chunks: lista de dicts com chaves 'source', 'chunk_index', 'content'
    """
    model = model or config.GROQ_MODEL

    context = "\n\n".join(
        f"[{i + 1}] Fonte: {c['source']}\n{c['content']}"
        for i, c in enumerate(chunks)
    )
    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Pergunta: {query}\n\n"
                "---\n"
                f"Trechos relevantes dos documentos:\n{context}"
            ),
        },
    ]

    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1,
        max_tokens=800,
    )
    return resp.choices[0].message.content
