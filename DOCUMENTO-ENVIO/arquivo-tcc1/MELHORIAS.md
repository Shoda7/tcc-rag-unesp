> **Arquivado em 19/10/2026.** Revisão automática de 09/06 sobre a versão preliminar do TCC I (`tcc1_matheus_rafael.tex`).
> A maior parte dos itens já foi tratada; o que restou foi absorvido pela revisão de 14/10 (avaliação v2).
> A lista de pendências vigente está em `PLANO_TCC2_ATE_FEV_2027.md` (raiz do repositório).

# Revisão do TCC — Melhorias sugeridas

**Documento revisado:** `tcc1_matheus_rafael.tex` (TCC I — preliminar)
**Cruzado com:** `referencias.bib`, `README.md`, código-fonte (`src/`, `scripts/`, `.env`)
**Data da revisão:** 09/06/2026 · revisão automática (tarefa `validar-tcc`)

## Resumo

O texto está bem estruturado e coerente em termos de redação acadêmica (ABNT, resumo/abstract, objetivos, referencial, metodologia). Os problemas encontrados são, na maioria, **inconsistências entre o que o texto descreve e o que o sistema realmente implementa**, além de **um erro que impede a compilação no LaTeX**. Nada disso é grave, mas todos devem ser corrigidos antes da entrega final para evitar questionamentos da banca.

---

## 1. Bloqueia a compilação (corrigir primeiro)

**1.1 Pacote `enumitem` não está carregado.**
O documento usa `\begin{enumerate}[label=\alph*)]` em três pontos (linhas 150, 198 e 220), mas nenhum pacote que suporte essa sintaxe está no preâmbulo. A sintaxe `label=\alph*)` é exclusiva do `enumitem`; sem ele o pdfLaTeX aborta com erro.

**Correção:** adicionar no preâmbulo (junto aos demais `\usepackage`):

```latex
\usepackage{enumitem}
```

---

## 2. Inconsistências entre o texto e o sistema implementado

Estas são as mais importantes — a banca tende a comparar o que está escrito com o repositório.

**2.1 Modelo de embeddings e dimensão (alta prioridade).**
O texto (Seção *Fase 2: Indexação*, e o Referencial) afirma que o sistema usa o `multilingual-e5-large` com **1024 dimensões**. Porém o sistema realmente executado usa o `intfloat/multilingual-e5-small` com **384 dimensões** (ver `.env`: `EMBEDDING_MODEL=intfloat/multilingual-e5-small`, `EMBEDDING_DIM=384`; o `README.md` também cita e5-small/384). 

Há, portanto, divergência tripla: texto (e5-large/1024) × `.env`/README (e5-small/384) × `config.py` (default e5-large). **Decidir qual modelo de fato será reportado** e uniformizar texto, `.env`, `README.md` e `config.py`. Se a avaliação do README (Hit@5 = 0,90 no híbrido) foi obtida com o e5-small, o texto precisa citar e5-small/384, não e5-large/1024.

**2.2 Métricas de avaliação (alta prioridade).**
O resumo, o objetivo específico (e) e a *Fase 4* descrevem as métricas como **Precision@K, Recall@K e MRR**. O código real (`scripts/evaluate.py`) calcula **Hit@1, Hit@3, Hit@5, MRR e latência** — não calcula Precision nem Recall. 

**Correção:** alinhar o texto às métricas efetivamente implementadas (Hit@K + MRR + latência), ou implementar Precision/Recall se quiser mantê-las. Recomenda-se ajustar o texto, pois Hit@K é adequado para um *eval set* com poucos documentos relevantes por query.

**2.3 Método híbrido (RRF) ausente na metodologia (média/alta prioridade).**
A questão de pesquisa e o objetivo geral comparam apenas **busca vetorial × BM25 (FTS)**. No entanto, o sistema implementado avalia **três** métodos — vetorial, FTS e **híbrido por Reciprocal Rank Fusion (RRF)** — e o melhor resultado do projeto é justamente o híbrido (Hit@5 = 0,90, MRR = 0,697, conforme README). O texto subdimensiona a própria contribuição. 

**Correção:** incluir a busca híbrida RRF como terceiro braço na questão de pesquisa, nos objetivos e na *Fase 4*, e citar a fonte do RRF (Cormack et al., 2009 — listada no README mas **ausente do `referencias.bib`**).

**2.4 Provedor do LLM em produção (média prioridade).**
O capítulo *Desenvolvimento* descreve apenas o protótipo com **LLaMA 3 via Ollama (local)**. O sistema de produção (`src/llm.py`, `.env`) usa **Groq** com o modelo **`llama-3.3-70b-versatile`** (API compatível com OpenAI). O texto não menciona o Groq em momento algum. 

**Correção:** acrescentar, na arquitetura de produção, que a geração é feita via Groq (`llama-3.3-70b-versatile`), deixando claro o que é protótipo (Ollama) e o que é produção (Groq).

**2.5 Contagem de documentos (baixa prioridade).**
O texto diz "aproximadamente **937** documentos" (Fase 1); o README diz **936** resoluções. Uniformizar para o número exato realmente indexado (e, se útil, citar também os 17 PDFs curriculares e os **4229 chunks** resultantes, número já presente no README).

---

## 3. Itens de revisão final (pré-textuais e pendências esperadas)

Itens normais de uma versão preliminar, mas que **não podem ficar para depois da entrega final**:

- **Folha de aprovação:** ainda contém os marcadores `[Nome do Membro Titular]` (linhas 96–97). Preencher os nomes da banca antes da defesa.
- **Cronograma:** confira a coerência das datas com o calendário real de TCC I/II (a faixa "Escrita TCC I" vai até agosto, mas a entrega preliminar é em junho de 2026).

---

## 4. Pontos positivos (manter)

- Resumo e *Abstract* completos, bem escritos e com palavras-chave/keywords.
- Referencial teórico bem amarrado às 7 referências do `.bib` (todas as `\cite` têm entrada correspondente — verificado).
- Estrutura ABNT correta (abntex2, pré-textual/textual/pós-textual, fontes TNR 12pt).
- Metodologia em fases claras e justificativa sólida.

---

## Checklist rápido de correção

- [ ] Adicionar `\usepackage{enumitem}` (item 1.1) — **sem isso não compila**
- [ ] Uniformizar modelo de embeddings/dimensão em texto, `.env`, README e `config.py` (2.1)
- [ ] Alinhar métricas do texto às do código: Hit@K + MRR + latência (2.2)
- [ ] Incluir busca híbrida RRF na metodologia e nos objetivos (2.3)
- [ ] Adicionar entrada do RRF (Cormack et al., 2009) ao `referencias.bib` (2.3)
- [ ] Mencionar Groq / `llama-3.3-70b-versatile` na produção (2.4)
- [ ] Uniformizar contagem de documentos (936/937) (2.5)
- [ ] Preencher nomes da banca na folha de aprovação (3)
