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
     ├── BM25            (bm25.py, sobre os lexemas da coluna tsvector)
     ├── FTS-PG          (tsvector + unaccent, GIN, ts_rank_cd — baseline)
     └── híbrido RRF     (Reciprocal Rank Fusion: vetorial + BM25)
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

O `.env` não é versionado. Crie a partir do exemplo e preencha a chave do Groq:

```powershell
Copy-Item .env.example .env
# depois edite o .env:
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

# Busca lexical BM25
python -m src.pipeline bm25 "aproveitamento de estudos"

# Busca textual nativa do PostgreSQL (ts_rank_cd)
python -m src.pipeline fts "aproveitamento de estudos"

# Busca híbrida RRF (vetorial + BM25)
python -m src.pipeline hybrid "reingresso na graduação"

# RAG completo (híbrido RRF + geração com LLM)
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

O seletor no rodapé permite alternar entre **Híbrido (RRF)**, **Vetorial**, **BM25** e **FTS (PostgreSQL)**.

---

## Avaliação experimental

```powershell
# Roda os 4 métodos nas 50 queries anotadas, com testes de significância
python scripts/evaluate.py --csv data/resultados_avaliacao.csv --json data/resultados_resumo.json

# Regenera o documento do TCC (as tabelas são lidas do JSON acima)
node scripts/gerar_tcc.mjs
```

Métricas calculadas sobre os **5 primeiros documentos distintos** (a partir dos 50 primeiros chunks
de cada método). Latência medida após aquecimento do modelo.

**Resultados (50 queries, k=5, rodada de 14/10/2026):**

| Métrica        | Vetorial | FTS-PG | BM25  | Híbrido RRF |
|----------------|----------|--------|-------|-------------|
| Hit@1          | 0.560    | 0.320  | 0.660 | **0.700**   |
| Hit@3          | 0.780    | 0.560  | 0.760 | **0.880**   |
| Hit@5          | **0.900**| 0.640  | 0.840 | **0.900**   |
| MRR            | 0.690    | 0.439  | 0.718 | **0.785**   |
| Lat. mediana   | ~104 ms  | ~85 ms | ~6 ms | ~109 ms     |

Comparações pareadas do MRR (teste de aleatorização, p ajustado por Holm): RRF × Vetorial p=0.109,
RRF × BM25 p=0.259, Vetorial × BM25 p=0.646, BM25 × FTS-PG p<0.001. Ou seja, com 50 queries só a
diferença BM25 × FTS-PG é significativa no conjunto completo.

Por tipo de query (MRR):

| Tipo           | Vetorial | FTS-PG | BM25      | Híbrido RRF |
|----------------|----------|--------|-----------|-------------|
| Lexical (26)   | 0.849    | 0.641  | **0.897** | 0.849       |
| Semântica (24) | 0.518    | 0.220  | 0.524     | **0.715**   |

Nas semânticas, o RRF supera vetorial (p=0.045) e BM25 (p=0.025) após Holm.

> Os números da versão preliminar (junho/2026) estavam distorcidos: o "FTS (BM25)" usava `ts_rank_cd`
> (não é BM25) com termos ligados por E, o que zerava 22 das 50 queries, e a latência média incluía
> o carregamento do modelo. Detalhes em `PLANO_TCC2_ATE_FEV_2027.md`.

---

## Estrutura do repositório

```
app/
  main.py           # backend FastAPI
data/
  legislacao/       # 936 resoluções UNESP (.txt)
  eval_set.json     # 50 queries anotadas para avaliação
  resultados_avaliacao.csv   # resultados por query
  resultados_resumo.json     # métricas agregadas + testes (lido pelo gerar_tcc.mjs)
frontend/           # React + Vite (interface de chat)
scripts/
  scrape_legislacao.py   # coleta do portal legislação UNESP
  evaluate.py            # avaliação experimental (4 métodos + significância)
  gerar_tcc.mjs          # gera DOCUMENTO-ENVIO/TCC_RAG_UNESP_Bauru.docx
src/
  config.py         # variáveis de ambiente
  chunk.py          # segmentação sliding window
  bm25.py           # BM25 Okapi sobre os lexemas do PostgreSQL
  db.py             # PostgreSQL + pgvector (schema, busca vetorial/FTS/BM25/RRF)
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
- Clarke, Cormack & Tudhope (2000) — *Relevance ranking for one to three term queries* (ts_rank_cd)
- Smucker, Allan & Carterette (2007) — *A comparison of statistical significance tests for IR evaluation*
- Cormack et al. (2009) — *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods*
