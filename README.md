# Sistema RAG — Documentos Regulatórios da UNESP Bauru

Implementação e avaliação de um sistema de **Recuperação Aumentada por Geração (RAG)**
para consulta em linguagem natural de documentos regulatórios da UNESP Bauru.

Projeto de TCC — Bacharelado em Sistemas de Informação.
Discentes: Matheus Shoda Lima · Rafael Panhozzi Rubio.

## Arquitetura do pipeline de indexação

```
[Portal UNESP]  ->  scraper  ->  PDFs (data/raw)
                                    |
                                  extract  ->  texto limpo (data/processed)
                                    |
                                  chunk (sliding window)
                                    |
                                  embeddings (modelo local: multilingual-e5-large)
                                    |
                                  PostgreSQL + pgvector  (tabela `chunks`)
```

A coluna `chunks.embedding` (vetorial, índice HNSW) sustenta a **busca vetorial**.
A coluna `chunks.content_tsv` (tsvector, índice GIN) já fica pronta para o
**baseline Full-Text Search** que será implementado na fase seguinte.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Coleta | `requests` + `beautifulsoup4` (crawler do portal) |
| Extração | `pdfplumber` |
| Embeddings | `sentence-transformers` (modelo local, sem custo de API) |
| Banco vetorial | PostgreSQL 16 + `pgvector` (via Docker) |

## Pré-requisitos

- Python 3.11+ (testado em 3.14)
- Docker Desktop

## Setup

```powershell
# 1. Ambiente virtual + dependências
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configuração
Copy-Item .env.example .env   # ajuste SCRAPER_SEEDS, modelo, etc.

# 3. Subir o banco (PostgreSQL + pgvector)
docker compose up -d
```

## Uso

Todos os comandos passam pelo orquestrador `src.pipeline`:

```powershell
# Baixar PDFs do portal da UNESP (configure SCRAPER_SEEDS no .env)
python -m src.pipeline scrape

# Extrair e limpar o texto dos PDFs baixados
python -m src.pipeline extract

# Chunking + embeddings + armazenamento no banco
python -m src.pipeline index

# Atalho: extract + index (se os PDFs já estão em data/raw)
python -m src.pipeline all

# Estado atual da base
python -m src.pipeline status

# Consulta de teste (recuperação vetorial)
python -m src.pipeline search "Qual o prazo de entrega do TCC?"
```

> Se preferir não usar o scraper, basta colocar os PDFs manualmente em
> `data/raw/` e rodar `python -m src.pipeline all`.

## Estrutura

```
src/
  config.py      # configuração via .env
  scraper.py     # coleta de PDFs no portal (crawler BFS)
  extract.py     # PDF -> texto limpo
  chunk.py       # segmentação sliding window
  embeddings.py  # embeddings locais (sentence-transformers)
  db.py          # PostgreSQL + pgvector (esquema, inserção, busca)
  pipeline.py    # CLI orquestrador
data/
  raw/           # PDFs baixados (+ manifest.json com a origem de cada um)
  processed/     # texto extraído e limpo
docker-compose.yml
requirements.txt
```

## Mapa com o cronograma do TCC

- **Atividade 3 — Coleta e pré-processamento:** `scraper.py` + `extract.py` + `chunk.py`
- **Atividade 5 — Pipeline de indexação (chunking + embeddings):** `chunk.py` + `embeddings.py` + `db.py`
- **Julho em diante:** pipeline de consulta RAG (LLM), baseline Full-Text Search e avaliação comparativa.
