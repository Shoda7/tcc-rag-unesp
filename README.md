# Sistema RAG — Documentos Regulatórios da UNESP Bauru

Implementação e avaliação de um sistema de **Recuperação Aumentada por Geração (RAG)**
para consulta em linguagem natural de documentos regulatórios da UNESP Bauru.

**TCC — Bacharelado em Sistemas de Informação · UNESP Bauru**
Discentes: Matheus Shoda Lima · Rafael Panhozzi Rubio

---

## Arquitetura

```
[sistemas.unesp.br/legislacao-web]
        |
   scrape_legislacao.py  →  data/legislacao/*.txt  (936 resoluções)
        |
   chunk.py (sliding window 350 palavras, overlap 60)
        |
   embeddings.py (intfloat/multilingual-e5-small, 384 dims, local)
        |
   PostgreSQL 16 + pgvector
     ├── busca vetorial  (HNSW, similaridade cossenoidal)
     ├── FTS / BM25      (tsvector + unaccent, índice GIN)
     └── híbrido RRF     (Reciprocal Rank Fusion)
        |
   FastAPI (app/main.py)
        |
   React + Vite (frontend/)
```

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Python | 3.11 |
| Node.js | 18 |
| Docker Desktop | qualquer recente |

---

## Setup rápido

### 1. Clone e ambiente Python

```powershell
git clone <repo-url>
cd TCC
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

Copie `.env` e preencha sua chave do Groq:

```powershell
# .env já existe no repositório — ajuste apenas:
GROQ_API_KEY=gsk_...        # obtenha em console.groq.com (free tier)
```

### 3. Banco de dados (PostgreSQL + pgvector)

```powershell
docker compose up -d
```

Aguarde ~10 s e verifique:

```powershell
docker compose ps   # State deve ser "running"
```

### 4. Indexar os documentos

Os textos já estão em `data/legislacao/` (936 resoluções UNESP).
Rode uma única vez para popular o banco:

```powershell
python -m src.pipeline index
# ~16 min na CPU; exibe progresso em tempo real
```

Verifique:

```powershell
python -m src.pipeline status
# Chunks no banco: 4229
```

---

## Uso via CLI

```powershell
# Busca vetorial
python -m src.pipeline search "Quais são as normas para TCC?"

# Busca FTS (BM25)
python -m src.pipeline fts "aproveitamento de estudos"

# Busca híbrida RRF
python -m src.pipeline hybrid "reingresso na graduação"

# RAG completo (recuperação + geração com LLM)
python -m src.pipeline ask "Como funciona o calendário escolar de 2025?"
```

---

## Interface web (biblioteca)

### Backend

```powershell
# Na raiz do projeto, com .venv ativo:
uvicorn app.main:app --reload --port 8000
```

Endpoints disponíveis:
- `POST /api/ask` — RAG completo (embed → RRF → LLM)
- `POST /api/search` — só recuperação (sem LLM)
- `GET  /api/health` — healthcheck

Documentação interativa: http://localhost:8000/docs

### Frontend

```powershell
cd frontend
npm install   # apenas na primeira vez
npm run dev
```

Abra http://localhost:5173 no navegador.

O seletor no rodapé permite alternar entre **Híbrido (RRF)**, **Vetorial** e **FTS (BM25)**.

---

## Avaliação experimental

```powershell
# Roda os 3 métodos nas 50 queries anotadas e exporta CSV
python scripts/evaluate.py --csv data/resultados_avaliacao.csv
```

**Resultados obtidos (50 queries, k=5):**

| Métrica   | Vetorial | FTS (BM25) | Híbrido RRF |
|-----------|----------|-----------|-------------|
| Hit@1     | 0.520    | 0.400     | **0.560**   |
| Hit@3     | 0.740    | 0.520     | **0.840**   |
| Hit@5     | 0.840    | 0.520     | **0.900**   |
| MRR       | 0.642    | 0.457     | **0.697**   |
| Lat. média| ~339 ms  | ~4 ms     | ~348 ms     |

Por tipo de query:

| Tipo     | Método   | Hit@1 | MRR   |
|----------|----------|-------|-------|
| Lexical  | FTS      | 0.731 | **0.840** |
| Lexical  | Vetorial | 0.654 | 0.758 |
| Semântico| Vetorial | **0.375** | **0.517** |
| Semântico| FTS      | 0.042 | 0.042 |

---

## Estrutura do repositório

```
app/
  main.py           # backend FastAPI
data/
  legislacao/       # 936 resoluções UNESP (.txt)
  eval_set.json     # 50 queries anotadas para avaliação
  resultados_avaliacao.csv
frontend/           # React + Vite (interface de chat)
scripts/
  scrape_legislacao.py   # coleta do portal legislação UNESP
  evaluate.py            # avaliação experimental
src/
  config.py         # variáveis de ambiente
  chunk.py          # segmentação sliding window
  db.py             # PostgreSQL + pgvector (schema, busca vetorial/FTS/RRF)
  embeddings.py     # embeddings locais (sentence-transformers)
  llm.py            # geração de respostas via Groq
  pipeline.py       # CLI orquestrador
docker-compose.yml
requirements.txt
```

---

## Referências principais

- Lewis et al. (2020) — *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (NeurIPS)
- Gao et al. (2023) — *RAG for LLMs: A Survey* (arXiv:2312.10997)
- Robertson & Zaragoza (2009) — *The Probabilistic Relevance Framework: BM25 and Beyond*
- Cormack et al. (2009) — *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods*
