# TCC — plano em etapas até a entrega (fev/2027)

**Atualizado em:** 14/10/2026
**Calendário:** a greve reprogramou o calendário acadêmico; a entrega final passou para **fevereiro de 2027**.
**Documento vigente:** `DOCUMENTO-ENVIO/TCC_RAG_UNESP_Bauru.docx`, gerado por `node scripts/gerar_tcc.mjs`. As tabelas e os números do texto vêm de `data/resultados_resumo.json`.

## Como usar

- Para começar uma etapa, diga **"faça a etapa N"**.
- Ao terminar uma etapa, eu marco `[x]` nela, anoto a data e digo qual é a próxima.
- Etapas da mesma "onda" que não dependem uma da outra podem ser feitas em qualquer ordem.
- **Quem faz:**
  - **Claude**: eu faço sozinho;
  - **Vocês**: precisa ser feito por vocês (anotação, contato com o orientador, decisões);
  - **Ambos**: eu preparo e vocês executam ou validam.

## Visão geral

| Nº | Etapa | Quem | Depende de | Quando |
|---|---|---|---|---|
| 0 | Correções da avaliação e do texto | Claude | — | ✅ 14/10 |
| 1 | Commit e organização do repositório | Claude | 0 | ✅ 19/10 |
| 2 | Revisão do documento e contato com o orientador | Ambos | 1 | 🔄 lado do Claude feito em 19/10; faltam vocês |
| 3 | Congelar o corpus (reprodutibilidade) | Ambos | 1 | out |
| 4 | Planilhas de julgamento de relevância (*pooling*) | Ambos | 1 | fim de out–nov |
| 5 | Coleta de perguntas reais de alunos | Ambos | 2 (resposta sobre CEP) | nov |
| 6 | Reavaliação com julgamentos múltiplos | Claude | 4 (e 5, se houver) | nov |
| 7 | Preparar o experimento de geração | Ambos | 1 | nov |
| 8 | Anotar as respostas geradas | Vocês | 7 | nov–dez |
| 9 | Análise da geração e texto do capítulo | Claude | 8 | dez |
| 10 | Trabalhos Relacionados e referências | Ambos | — | nov–dez |
| 11 | Figuras e capítulo de Desenvolvimento | Claude | 1 | nov–dez |
| 12 | Formatação final no modelo BSI | Ambos | 2, 6, 9, 10, 11 | jan |
| 13 | Revisão final e versão para o orientador | Ambos | 12 | meados de jan |
| 14 | Apresentação para a banca | Ambos | 13 | fim de jan–fev |
| 15 | Pós-banca e depósito | Ambos | banca | fev |
| X | *(Opcional)* Ablações: embeddings maiores e reranker | Claude | 6 | se sobrar tempo |

**Ondas** (tudo dentro de uma onda pode correr em paralelo):

| Onda | Etapas |
|---|---|
| A | 1 → 2 e 3 |
| B | 4, 5, 7, 10, 11 |
| C | 6, 8 → 9 |
| D | 12 → 13 → 14 → 15 |

---

## Etapa 0 — Correções da avaliação e do texto ✅ (14/10/2026)

O que foi feito (detalhes no README e no histórico):

- **Busca e avaliação:**
  - BM25 real em `src/bm25.py`;
  - FTS do PostgreSQL com semântica OU (OR);
  - híbrido = vetorial + BM25;
  - `hnsw.ef_search = 200`;
  - métricas sobre documentos distintos;
  - latência medida após aquecimento;
  - testes de significância (aleatorização + Holm) e IC por *bootstrap*;
  - `evaluate.py --json` alimenta as tabelas do documento.
- **Correções de código:** `smoke_db.py` não apaga mais o índice real; `pipeline ask` usa o híbrido; `.env.example` e README corrigidos; API e frontend com a opção BM25.
- **Texto do TCC:**
  - Resumo/Abstract, objetivos, escopo e caps. 2–4 revisados;
  - novo Cap. 5 (Considerações Finais);
  - cronograma até fev/2027;
  - 5 referências novas;
  - campo do sumário corrigido.

Resultados v2 (MRR, 50 consultas):

| | Vetorial | FTS-PG | BM25 | Híbrido RRF |
|---|---|---|---|---|
| Geral | 0,690 | 0,439 | 0,718 | **0,785** |
| Semânticas (24) | 0,518 | 0,220 | 0,524 | **0,715** |
| Lexicais (26) | 0,849 | 0,641 | **0,897** | 0,849 |

O híbrido lidera, mas no conjunto completo não há significância contra a vetorial nem contra o BM25. Nas consultas semânticas há significância (p = 0,045 e p = 0,025, com Holm). BM25 × FTS-PG: p < 0,001.

---

## Etapa 1 — Commit e organização do repositório ✅ (19/10/2026)

- [x] **Quem:** Claude · **Depende de:** 0
- **Eu faço:**
  - revisar o diff pendente e commitar em commits separados: (a) BM25 e avaliação v2; (b) correções de código; (c) texto do TCC + documento; (d) README e plano;
  - criar a tag `avaliacao-v2` no commit dos resultados;
  - mover as versões antigas (`tcc1_matheus_rafael.tex`, `referencias.bib`, `TCC1_*`, `MELHORIAS.md`) para `DOCUMENTO-ENVIO/arquivo-tcc1/`.
- **Vocês fazem:** decidir se querem um remoto (GitHub) para backup: hoje o repositório só existe nesta máquina.
- **Pronto quando:** o `git status` estiver limpo e a tag existir.
- **Feito em 19/10:**
  - 5 commits: BM25 + avaliação v2 · correções de API/CLI/smoke test · documento do TCC · arquivamento do TCC I · README + plano;
  - tag `avaliacao-v2` no commit dos resultados (`889c928`);
  - versões antigas do TCC I movidas para `DOCUMENTO-ENVIO/arquivo-tcc1/` (o `.tex` continua ao lado do `.bib`);
  - **sem `push`:** não há remoto configurado. Se criarem um repositório no GitHub, eu adiciono o remoto e envio os commits e a tag.

## Etapa 2 — Revisão do documento e contato com o orientador 🔄 (parte do Claude concluída em 19/10/2026)

- [ ] **Quem:** Ambos · **Depende de:** 1
- **Eu fiz (19/10):**
  - **Releitura do documento contra os dados.** Correções:
    - "intervalos dos três primeiros métodos" → vetorial, BM25 e híbrido (o IC do FTS-PG não se sobrepõe ao do BM25);
    - a frase "p95 abaixo de 200 ms" passou a ser calculada a partir do JSON;
    - "código e resultados estão disponíveis no repositório" → "serão disponibilizados" (o repositório não é público);
    - Objetivo Geral alinhado ao número de métodos;
    - data de acesso da referência nova.
  - **Referências novas conferidas na web:** Clarke et al. (2000), Holm (1979), Smucker et al. (2007), Malkov e Yashunin (2020) e Wang et al. (2024) estão com título, veículo e páginas corretos.
  - **Sumário:** "Resumo", "Abstract" e "Sumário" saíram da lista (ABNT), e o `scripts/finalizar_docx.ps1` faz o Word preencher o sumário e exportar o PDF. O `.docx` agora já vem com o sumário atualizado (34 entradas).
  - **PDF para o orientador:** `DOCUMENTO-ENVIO/TCC_RAG_UNESP_Bauru_rascunho_2026-10-19.pdf` (25 páginas).
  - **Rascunho da mensagem:** `DOCUMENTO-ENVIO/mensagem_orientador_2026-10-19.md`.
- **Vocês fazem:**
  - ler o PDF, principalmente os caps. 4 e 5 (texto novo), e dizer o que quiserem mudar;
  - ajustar e enviar a mensagem ao Prof. Clayton (com o PDF anexo);
  - trazer as respostas e registrá-las na tabela abaixo.
- **Pronto quando:** as respostas estiverem registradas aqui.

| Pergunta ao orientador | Resposta |
|---|---|
| 1. Data de entrega/depósito e da banca em fev/2027; membros da banca | _(a preencher)_ |
| 2. Modelo Word oficial do BSI ou documento atual | _(a preencher)_ |
| 3. Perguntas anônimas de alunos exigem CEP? (afeta a Etapa 5) | _(a preencher)_ |
| 4. Título: manter "UNESP Bauru" ou ajustar para "UNESP" | _(a preencher)_ |
| 5. Retorno sobre o TCC I | _(a preencher)_ |

## Etapa 3 — Congelar o corpus

- [ ] **Quem:** Ambos · **Depende de:** 1
- **Eu faço:**
  - criar o `scripts/snapshot_corpus.py`, que gera um zip de `data/legislacao/` + `manifest.json` + `eval_set.json` com hash SHA-256;
  - registrar o hash no README e citá-lo na metodologia.
- **Vocês fazem:** escolher onde publicar (GitHub Release ou Zenodo, que gera DOI) e autorizar a publicação.
- **Pronto quando:** o pacote estiver publicado e o link e o hash constarem no README e no texto.

## Etapa 4 — Planilhas de julgamento de relevância (*pooling*)

- [ ] **Quem:** Ambos · **Depende de:** 1
- **Eu faço:**
  - criar o `scripts/pooling.py`: para cada consulta, junta os 5 primeiros documentos de cada um dos 4 métodos (cerca de 10 documentos distintos por consulta);
  - exportar **uma planilha por anotador** com: consulta, título e trecho da resolução, coluna de relevância (0 = irrelevante, 1 = parcialmente relevante, 2 = relevante). A ordem é embaralhada, para não revelar o método;
  - escrever um guia de anotação de 1 página.
- **Vocês fazem:** Matheus e Rafael anotam **separadamente, sem conversar**. São cerca de 500 julgamentos por pessoa, umas 3 a 4 horas cada.
- **Pronto quando:** as duas planilhas estiverem preenchidas em `data/julgamentos/`.

## Etapa 5 — Coleta de perguntas reais de alunos

- [ ] **Quem:** Ambos · **Depende de:** 2 (resposta sobre CEP)
- **Eu faço:**
  - escrever o texto do formulário (anônimo, sem dados pessoais) e as instruções ("escreva dúvidas reais sobre regras da UNESP, sem consultar os documentos");
  - depois da coleta: filtrar as perguntas fora do escopo e preparar o `eval_set` ampliado;
  - rodar o *pooling* (Etapa 4) para as perguntas novas.
- **Vocês fazem:** divulgar o formulário (colegas, centro acadêmico, biblioteca) e juntar **30 ou mais perguntas**. Depois, anotar a relevância das perguntas novas.
- **Pronto quando:** houver 80–100 consultas com julgamentos.
- **Se não der tempo ou não for autorizado:** seguir só com as 50 consultas atuais e declarar isso como limitação.

## Etapa 6 — Reavaliação com julgamentos múltiplos

- [ ] **Quem:** Claude · **Depende de:** 4 (e 5, se houver)
- **Eu faço:**
  - calcular a concordância entre os anotadores (kappa de Cohen) e consolidar os julgamentos (regra para as divergências);
  - adaptar o `evaluate.py` para vários documentos relevantes por consulta e incluir **nDCG@5** e **Recall@5**;
  - rodar tudo de novo, regenerar o documento e atualizar os caps. 3 e 4 (descrição do *pooling*, kappa e novas tabelas);
  - criar a tag `avaliacao-v3`.
- **Pronto quando:** o documento estiver regenerado com os resultados v3 e o texto coerente com eles.

## Etapa 7 — Preparar o experimento de geração

- [ ] **Quem:** Ambos · **Depende de:** 1
- **Eu faço:**
  - confirmar se o `llama-3.3-70b-versatile` está disponível no Groq e registrar o modelo e a data;
  - criar o `scripts/gerar_respostas.py` com cerca de 40 perguntas (30 do conjunto de avaliação + **10 sem resposta no corpus**, que eu proponho) em 3 condições:
    - LLM sem recuperação;
    - RAG vetorial;
    - RAG híbrido;
  - salvar a resposta, o contexto usado, a latência e os tokens de cada execução;
  - exportar a **planilha de anotação às cegas** (condição oculta, ordem embaralhada) e a chave separada;
  - escrever um guia com os critérios: correção (0–2), alucinação (sim/não), citação correta (sim/não), recusa adequada (para as perguntas sem resposta).
- **Vocês fazem:** confirmar que as 10 perguntas "sem resposta" realmente não são respondidas pelo corpus.
- **Pronto quando:** a planilha de anotação estiver gerada em `data/geracao/`.

## Etapa 8 — Anotar as respostas geradas

- [ ] **Quem:** Vocês · **Depende de:** 7
- **Vocês fazem:**
  - os dois anotam as cerca de 120 respostas (40 perguntas × 3 condições) **separadamente**, seguindo o guia;
  - estimativa: 2 a 3 horas por pessoa.
- **Eu faço:** tiro dúvidas sobre os critérios durante a anotação, se precisarem.
- **Pronto quando:** as duas planilhas estiverem preenchidas.

## Etapa 9 — Análise da geração e texto do capítulo

- [ ] **Quem:** Claude · **Depende de:** 8
- **Eu faço:**
  - calcular o kappa por critério e, para cada condição: taxa de alucinação, correção média, citação correta, recusa adequada e latência;
  - fazer testes pareados entre as condições;
  - acrescentar as tabelas ao JSON e ao documento;
  - escrever a seção "Avaliação da Geração" (metodologia + resultados + discussão);
  - atualizar o Resumo/Abstract e as Considerações Finais. Isso cumpre o objetivo (f).
- **Pronto quando:** o documento estiver regenerado com o capítulo da geração.

## Etapa 10 — Trabalhos Relacionados e referências

- [ ] **Quem:** Ambos · **Depende de:** — (pode começar a qualquer momento)
- **Eu faço:**
  - pesquisar e propor de 8 a 12 trabalhos com fichamento curto (problema, método, resultado, relação com o TCC);
  - temas: RAG em português, RAG em domínio jurídico/institucional, busca densa × BM25 (DPR, BEIR), avaliação de RAG (RAGAS), Llama 3;
  - redigir o capítulo "Trabalhos Relacionados" e acrescentar as referências em ABNT, conferidas, com a meta de **20 ou mais** no total.
- **Vocês fazem:** ler pelo menos o resumo dos trabalhos citados (a banca pergunta) e aprovar a seleção.
- **Pronto quando:** o capítulo estiver no documento e todas as referências forem citadas e conferidas.

## Etapa 11 — Figuras e capítulo de Desenvolvimento

- [ ] **Quem:** Claude · **Depende de:** 1
- **Eu faço:**
  - diagrama da arquitetura (coleta → indexação → 4 métodos → API → interface);
  - gráficos do corpus (resoluções por ano, distribuição de tamanho);
  - **capturas de tela da interface** (vou rodar o backend e o frontend no navegador);
  - inserir tudo no documento com legenda e "Fonte:", e redigir a seção que descreve a implementação (módulos, API, prompt do sistema).
- **Pronto quando:** as figuras estiverem no documento e citadas no texto.

## Etapa 12 — Formatação final no modelo BSI

- [ ] **Quem:** Ambos · **Depende de:** 2 (decisão do formato), 6, 9, 10, 11
- **Eu faço:**
  - se o orientador exigir o modelo Word oficial, migrar o conteúdo para ele;
  - em qualquer caso: listas de tabelas, figuras e siglas; apêndices (conjunto de avaliação, prompt, exemplos de respostas); **ano da capa = 2027**; nomes da banca; cronograma "realizado";
  - conferir margens, espaçamento, legendas e citações ABNT.
- **Vocês fazem:** gerar a **ficha catalográfica** em biblioteca.unesp.br/ficha. Ela precisa dos dados de vocês e do número de páginas final.
- **Pronto quando:** o documento estiver completo no formato exigido.

## Etapa 13 — Revisão final e versão para o orientador

- [ ] **Quem:** Ambos · **Depende de:** 12
- **Eu faço:**
  - repetir a validação completa (texto × código × números, como na Etapa 0);
  - revisão de ortografia e ABNT;
  - gerar o PDF e uma lista de mudanças desde a última versão enviada.
- **Vocês fazem:** ler o documento inteiro e enviar ao orientador até **meados de janeiro**. Depois, trazer o feedback para eu incorporar.
- **Pronto quando:** o feedback do orientador estiver incorporado e o PDF de entrega gerado.

## Etapa 14 — Apresentação para a banca

- [ ] **Quem:** Ambos · **Depende de:** 13
- **Eu faço:**
  - slides com roteiro e tempo por slide;
  - roteiro da demonstração;
  - lista de perguntas prováveis da banca com respostas sugeridas: BM25 × FTS, viés do conjunto de avaliação, significância, escopo UNESP × Bauru, custo, LGPD.
- **Vocês fazem:**
  - gravar um **vídeo da demonstração** como reserva, caso o Docker ou o Groq falhem na hora;
  - ensaiar com cronômetro.
- **Pronto quando:** os slides estiverem prontos, o vídeo gravado e houver pelo menos um ensaio completo.

## Etapa 15 — Pós-banca e depósito

- [ ] **Quem:** Ambos · **Depende de:** banca
- **Eu faço:** incorporar as correções pedidas pela banca e gerar o PDF final.
- **Vocês fazem:** coletar as assinaturas da folha de aprovação, juntar a ficha catalográfica ao PDF e fazer o depósito.
- **Pronto quando:** o depósito estiver feito.

## Etapa X — *(Opcional)* Ablações

- [ ] **Quem:** Claude · **Depende de:** 6
- **Eu faço:**
  - reindexar em tabelas separadas com `multilingual-e5-base` (768) e `multilingual-e5-large` (1024);
  - testar o reranqueamento com *cross-encoder*;
  - variar o tamanho do chunk (250/500);
  - comparar com a configuração atual e acrescentar uma seção curta ao cap. 4.
- **Só fazer se:** as Etapas 6 e 9 estiverem prontas antes de dezembro.

---

## Observação sobre o ambiente

Em 14/10, o Docker Desktop 4.50 travou ao iniciar porque havia três *sockets* órfãos de 08/06:
- `Docker\run\dockerInference`
- `Docker\run\userAnalyticsOtlpHttp.sock`
- `docker-secrets-engine\engine.sock`

Eles foram removidos e o Docker voltou a funcionar, com o volume `tcc_pgdata` intacto.

O erro **voltou a aparecer em 19/10** (o Docker deixa os sockets para trás quando fecha sem desligar direito), então é recorrente. Para resolver, com um comando:

```powershell
powershell -File scripts\docker_reparar.ps1
```

O script encerra o Docker, remove os sockets órfãos pelo WSL e abre o Docker de novo, sem tocar nos volumes. Depois espere cerca de 1 minuto até o `docker ps` responder. Na janela de erro, clique em **Quit**, nunca em "Reset to factory defaults" (isso apaga todos os containers e volumes).

Há um backup do disco do Docker (3,8 GB) em `C:\Users\matheuslima\docker-backup-20261014\`. Pode ser apagado quando vocês quiserem.
