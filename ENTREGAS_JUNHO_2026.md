# Plano de Entregas — TCC RAG UNESP Bauru

**Sistema:** Implementação e Avaliação de um Sistema de Recuperação Aumentada por Geração (RAG) para Consulta de Documentos Regulatórios da UNESP Bauru

**Discentes:** Matheus Shoda Lima · Rafael Panhozzi Rubio

**Data de referência:** Junho de 2026 (mês 3 do cronograma de 9 meses)

---

## Contexto do cronograma

O projeto foi escrito em **abril/2026** e a entrega final está prevista para **dezembro/2026**. O cronograma de 9 meses mapeia no calendário assim:

| Mês cronograma | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|----------------|---|---|---|---|---|---|---|---|---|
| Calendário     | Abr | Mai | **Jun** | Jul | Ago | Set | Out | Nov | Dez |

**Estamos no mês 3 (junho).** Tudo marcado nas colunas 1, 2 e 3 do cronograma original precisa estar entregue/em andamento até o fim deste mês.

### Atividades que vencem até o fim de junho

| # | Atividade | Meses (cronograma) | Status esperado |
|---|-----------|--------------------|-----------------|
| 1 | Levantamento bibliográfico e revisão de literatura | 1–2 | ✅ Concluído |
| 2 | Estudo das tecnologias (embeddings, bancos vetoriais, LLMs) | 1–3 | ✅ Concluindo |
| 3 | Coleta e pré-processamento dos documentos da UNESP | 2–3 | ✅ Concluindo |
| 4 | Escrita do TCC I (capítulos iniciais) | 2–5 | 🔄 Em andamento |
| 5 | Implementação do pipeline de indexação (chunking + embeddings) | 3–4 | 🔄 Iniciando |

> As atividades a partir do mês 4 (pgvector, pipeline RAG de consulta, Full-Text Search, experimentos, análise, TCC II e banca) **não são cobradas neste momento**.

---

## 1. Levantamento bibliográfico e revisão de literatura ✅

**Objetivo:** consolidar a fundamentação teórica que sustenta o capítulo de Referencial Teórico do TCC I.

### Passos

- [ ] **1.1 — Recuperar e organizar as referências-base já citadas no projeto**
  - Lewis et al. (2020) — RAG para tarefas NLP intensivas em conhecimento (NeurIPS)
  - Gao et al. (2023) — *Retrieval-Augmented Generation for LLMs: A Survey* (arXiv:2312.10997)
  - Ji et al. (2023) — *Survey of Hallucination in NLG* (ACM Computing Surveys)
  - Robertson & Zaragoza (2009) — BM25 (Probabilistic Relevance Framework)
  - Documentação do pgvector
- [ ] **1.2 — Buscar referências complementares** (Google Scholar / arXiv / IEEE / ACM) sobre:
  - Estratégias de chunking (fixed-size, sliding window, semantic chunking)
  - Modelos de embedding multilíngues/português (text-embedding-3-small, multilingual-e5-large, BERTimbau)
  - Métricas de avaliação de recuperação (Precision@K, Recall@K, MRR, nDCG)
  - Comparações empíricas entre busca densa (vetorial) e esparsa (BM25/FTS)
- [ ] **1.3 — Cadastrar todas as referências em um gerenciador** (Zotero ou Mendeley) já no formato ABNT.
- [ ] **1.4 — Fichar cada referência:** problema abordado, método, resultado e como se conecta ao trabalho.
- [ ] **1.5 — Redigir a seção "Revisão de Literatura / Referencial Teórico"** organizada nos eixos:
  - 3.1 LLMs e o problema das alucinações
  - 3.2 Recuperação Aumentada por Geração (RAG)
  - 3.3 Bancos de dados vetoriais e embeddings
  - 3.4 Busca textual tradicional (FTS/BM25) vs. busca vetorial

**Entregável:** capítulo de Referencial Teórico escrito + base de referências em ABNT no Zotero/Mendeley.

---

## 2. Estudo das tecnologias: embeddings, bancos vetoriais e LLMs ✅

**Objetivo:** dominar tecnicamente a stack antes de implementar, e justificar as escolhas no TCC.

### Passos

- [ ] **2.1 — Montar o ambiente de desenvolvimento**
  - Python 3.11+ com `venv`/`uv`
  - `requirements.txt` inicial: `langchain`, `psycopg2-binary` (ou `psycopg`), `pgvector`, `openai`, `tiktoken`, `python-dotenv`, `pypdf`/`pdfplumber`
  - Repositório Git versionado (recomendado já hospedar no GitHub)
- [ ] **2.2 — Estudar embeddings**
  - Como funcionam (representação densa, similaridade cossenoidal)
  - Comparar candidatos para português: `text-embedding-3-small` (OpenAI), `multilingual-e5-large` (Microsoft), BERTimbau
  - Definir critério de escolha (qualidade em PT-BR × custo × dimensão do vetor)
- [ ] **2.3 — Estudar bancos vetoriais**
  - Conceito de índice ANN (HNSW, IVFFlat)
  - Justificar a escolha do **pgvector** (PostgreSQL) — integra busca vetorial e FTS no mesmo SGBD, facilitando a comparação experimental
- [ ] **2.4 — Estudar LLMs e APIs**
  - Modelo gerador (ex.: GPT-4o-mini, Claude Haiku ou similar com bom custo-benefício)
  - Conceitos de janela de contexto, prompt de sistema, *grounding* na fonte
  - Estimativa de custo por chamada (manter dentro do teto de R$ 200 do projeto)
- [ ] **2.5 — Provas de conceito mínimas (notebooks)**
  - Gerar um embedding de uma frase e medir similaridade cossenoidal entre dois textos
  - Subir o PostgreSQL + extensão pgvector localmente (Docker) e inserir/consultar um vetor de teste
  - Fazer uma chamada simples à API do LLM

**Entregável:** ambiente funcional + notebooks de PoC + seção do TCC justificando as escolhas tecnológicas.

> **Dica:** suba o PostgreSQL via Docker para reprodutibilidade:
> ```bash
> docker run -d --name tcc-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg16
> ```

---

## 3. Coleta e pré-processamento dos documentos da UNESP ✅

**Objetivo:** construir a base documental curada que alimentará tanto o RAG quanto o baseline FTS.

### Passos

- [ ] **3.1 — Levantar e baixar os documentos públicos** do portal da UNESP Bauru:
  - Regimento Geral de Graduação
  - Regulamento de TCC do Bacharelado em Sistemas de Informação
  - Resoluções do CEPE relevantes
  - Normas de bolsas e editais acadêmicos
- [ ] **3.2 — Organizar os arquivos** em estrutura padronizada (ex.: `data/raw/`), com planilha de metadados (nome, tipo, órgão emissor, data, URL de origem).
- [ ] **3.3 — Converter PDF → texto** com `pdfplumber`/`pypdf`; para PDFs escaneados, aplicar OCR (`pytesseract`).
- [ ] **3.4 — Limpar o texto**
  - Remover cabeçalhos/rodapés repetidos, numeração de página, quebras de linha espúrias
  - Normalizar acentuação/encoding (UTF-8), espaços e caracteres de controle
  - Salvar texto limpo em `data/processed/`
- [ ] **3.5 — Segmentar em chunks (sliding window)**
  - Definir tamanho do chunk (ex.: 500–800 tokens) e sobreposição (ex.: 10–20%)
  - Justificar os parâmetros com base na literatura (Gao et al., 2023)
  - Preservar metadados de origem por chunk (documento, seção, posição) — essencial para citar a fonte na resposta
- [ ] **3.6 — Validar a base** (contagem de documentos, chunks, distribuição de tamanhos) e documentar o processo.

**Entregável:** base documental curada (`data/raw` + `data/processed`), script de pré-processamento e chunking reproduzível, e descrição do processo para a seção de Metodologia.

---

## 4. Escrita do TCC I — capítulos iniciais 🔄

**Objetivo:** produzir os capítulos iniciais da monografia (TCC I). Atividade contínua (meses 2–5), mas já deve ter texto consolidado em junho.

### Passos

- [ ] **4.1 — Obter o template oficial** da UNESP Bauru / normas ABNT da instituição.
- [ ] **4.2 — Estruturar o documento:**
  - Capa, folha de rosto, resumo/abstract, sumário
  - Introdução (problema de pesquisa, questão, objetivos)
  - Justificativa
  - Referencial Teórico (resultado da atividade 1)
  - Metodologia (descrição das 4 fases, já com o que foi definido nas atividades 2 e 3)
- [ ] **4.3 — Migrar e expandir** o conteúdo já existente no projeto de TCC para a monografia.
- [ ] **4.4 — Documentar decisões técnicas** tomadas nas atividades 2 e 3 (escolha de embedding, pgvector, parâmetros de chunking) dentro da Metodologia.
- [ ] **4.5 — Revisar normalização ABNT** (citações, referências, figuras, tabelas) com o gerenciador de referências.
- [ ] **4.6 — Submeter ao orientador** para feedback e registrar ajustes.

**Entregável:** rascunho avançado do TCC I com Introdução, Justificativa, Referencial Teórico e Metodologia escritos.

---

## 5. Implementação do pipeline de indexação (chunking + embeddings) 🔄

**Objetivo:** iniciar o pipeline que transforma os chunks em embeddings indexados. Começa no mês 3 (junho) e continua no mês 4 (julho) — em junho entrega-se a **parte inicial**.

### Passos (foco do que cabe em junho)

- [ ] **5.1 — Definir a arquitetura do pipeline** (diagrama): `documentos limpos → chunking → geração de embeddings → armazenamento`.
- [ ] **5.2 — Implementar o módulo de chunking** reutilizando o resultado da atividade 3 (parâmetros já definidos), com saída estruturada (chunk + metadados).
- [ ] **5.3 — Implementar a geração de embeddings**
  - Função que recebe um chunk e retorna o vetor pela API/modelo escolhido
  - Processamento em lote (*batching*) para reduzir custo e latência
  - Tratamento de erros e *rate limit*
- [ ] **5.4 — Definir o esquema de armazenamento** (tabela com `id`, `documento`, `texto_chunk`, `metadados`, `embedding vector(n)`) — a criação da tabela e índice no pgvector é o elo com a atividade do mês 4.
- [ ] **5.5 — Teste end-to-end reduzido:** indexar um subconjunto pequeno de documentos para validar o fluxo completo antes de escalar.

**Entregável:** módulos de chunking e geração de embeddings funcionando sobre uma amostra; esquema de dados definido; pipeline pronto para escalar em julho.

---

## Resumo do que entregar até 30/06/2026

1. ✅ **Revisão de literatura** escrita + referências ABNT organizadas.
2. ✅ **Estudo das tecnologias** concluído: ambiente montado, escolhas justificadas, PoCs rodando.
3. ✅ **Base documental** coletada, limpa e segmentada em chunks com metadados.
4. 🔄 **TCC I** com capítulos iniciais escritos (Introdução, Justificativa, Referencial, Metodologia).
5. 🔄 **Pipeline de indexação** iniciado: chunking + geração de embeddings funcionando em amostra.

> **Próximos passos (a partir de julho):** finalizar a indexação, implementar o banco vetorial pgvector, desenvolver o pipeline de consulta RAG e o baseline Full-Text Search.
