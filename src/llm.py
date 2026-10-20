"""Geração de respostas via Groq (componente G do pipeline RAG).

Groq expõe uma API compatível com OpenAI, então usamos o pacote `openai`
apontando para o endpoint do Groq. Modelo padrão: openai/gpt-oss-120b
(o llama-3.3-70b-versatile, usado até o início do TCC II, deixou de existir no Groq).

Duas condições de geração, usadas no experimento do TCC:
  - com recuperação (RAG): responde só com base nos trechos fornecidos;
  - sem recuperação (closed-book): responde com o conhecimento do próprio modelo.
"""
from __future__ import annotations

import time

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
    "por exemplo [resolucao_2023_0001.txt]; não use números nem qualquer outro formato "
    "de citação. Seja objetivo: responda em até 150 palavras. Responda em português."
)

# Versão 2 dos prompts (após o piloto de 19/10/2026, em que 10 de 22 respostas com recuperação
# usaram o formato de citação [n†L1-L9] e as respostas tinham mediana de ~430 palavras): a v2
# fixa o formato da citação e limita o tamanho. A condição sem recuperação recebe o mesmo limite.
_SYSTEM_SEM_CONTEXTO = (
    "Você é um assistente que responde perguntas sobre a Universidade Estadual Paulista (UNESP). "
    "Responda em português, de forma objetiva, em até 150 palavras. Se não souber ou não tiver "
    "certeza, diga claramente que não sabe, sem inventar informações."
)

_MAX_TENTATIVAS = 8


def _montar_mensagens(query: str, chunks: list[dict] | None) -> list[dict]:
    if not chunks:
        return [{"role": "system", "content": _SYSTEM_SEM_CONTEXTO},
                {"role": "user", "content": query}]
    context = "\n\n".join(
        f"[{i + 1}] Fonte: {c['source']}\n{c['content']}"
        for i, c in enumerate(chunks)
    )
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"Pergunta: {query}\n\n"
            "---\n"
            f"Trechos relevantes dos documentos:\n{context}"
        )},
    ]


def generate(query: str, chunks: list[dict] | None = None, model: str | None = None) -> dict:
    """Gera a resposta e devolve também os metadados da chamada.

    chunks: lista de dicts com 'source', 'chunk_index', 'content'; None ou vazia = sem recuperação.
    Em caso de limite de uso do plano gratuito (HTTP 429), espera o tempo indicado e tenta de novo.
    """
    from openai import RateLimitError

    model = model or config.GROQ_MODEL
    kwargs: dict = {"temperature": 0.1, "max_tokens": config.GROQ_MAX_TOKENS}
    if "gpt-oss" in model:
        kwargs["reasoning_effort"] = config.GROQ_REASONING_EFFORT

    messages = _montar_mensagens(query, chunks)
    client = _get_client()
    for tentativa in range(1, _MAX_TENTATIVAS + 1):
        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
            break
        except RateLimitError as exc:
            if tentativa == _MAX_TENTATIVAS:
                raise
            espera = float(exc.response.headers.get("retry-after", 20)) + 1.0
            if espera > 300:  # limite diario esgotado: esperar horas nao compensa; quem chamou decide
                raise
            print(f"    [limite do Groq] aguardando {espera:.0f}s (tentativa {tentativa}/{_MAX_TENTATIVAS})")
            time.sleep(espera)
    latencia = time.perf_counter() - t0

    choice = resp.choices[0]
    detalhes = getattr(resp.usage, "completion_tokens_details", None)
    return {
        "answer": choice.message.content or "",
        "model": resp.model,
        "finish_reason": choice.finish_reason,
        "prompt_tokens": resp.usage.prompt_tokens,
        "completion_tokens": resp.usage.completion_tokens,
        "reasoning_tokens": getattr(detalhes, "reasoning_tokens", None),
        "latency_s": round(latencia, 2),
    }


def ask(query: str, chunks: list[dict], model: str | None = None) -> str:
    """Gera resposta fundamentada nos chunks recuperados (usado pela API e pelo CLI)."""
    resposta = generate(query, chunks, model)["answer"]
    # o gpt-oss costuma citar com colchetes largos; padroniza para o formato do prompt
    return resposta.replace("【", "[").replace("】", "]")
