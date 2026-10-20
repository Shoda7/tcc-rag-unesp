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

## Decisões que tomei durante as etapas (vocês podem vetar)

1. **Modelo de linguagem: `openai/gpt-oss-120b`.** O `llama-3.3-70b-versatile` deixou de existir no Groq (`model_not_found` em 19/10) e o `/api/ask` estava quebrado. É o substituto mais próximo disponível (pesos abertos, 120 bi de parâmetros, mesmo plano gratuito). Editei o `.env` local (só a linha `GROQ_MODEL`) e o texto do TCC registra a troca. Para reverter ou testar outro modelo (`openai/gpt-oss-20b`, `qwen/qwen3.8-27b`), basta mudar `GROQ_MODEL`.
2. **Prompts v2.** O piloto de 33 respostas mostrou citações no formato `[1†L1-L9]` (10 de 22 respostas com recuperação) e respostas de ~430 palavras. O prompt agora fixa a citação pelo nome do arquivo e limita a 150 palavras. O piloto está arquivado em `data/geracao/respostas_piloto_v1.jsonl` e descrito no texto (3.4).
3. **Trabalhos Relacionados como seção 2.7**, e não como capítulo novo, para não renumerar o restante do texto.
4. **Interface:** passou a renderizar markdown (as respostas do modelo vêm formatadas) e ganhou os acentos que faltavam nos textos.
5. **10 perguntas "sem resposta" do experimento de geração:** escolhi e verifiquei por busca de palavras-chave; vocês confirmam (Etapa 7).

## Visão geral

| Nº | Etapa | Quem | Depende de | Quando |
|---|---|---|---|---|
| 0 | Correções da avaliação e do texto | Claude | — | ✅ 14/10 |
| 1 | Commit e organização do repositório | Claude | 0 | ✅ 19/10 |
| 2 | Revisão do documento e contato com o orientador | Ambos | 1 | 🔄 lado do Claude feito em 19/10; faltam vocês |
| 3 | Congelar o corpus (reprodutibilidade) | Ambos | 1 | 🔄 técnico feito em 19/10; falta publicar |
| 4 | Planilhas de julgamento de relevância (*pooling*) | Ambos | 1 | 🔄 planilhas prontas em 19/10; falta anotar |
| 5 | Coleta de perguntas reais de alunos | Ambos | 2 (resposta sobre CEP) | 🔄 texto do formulário pronto; faltam CEP e coleta |
| 6 | Reavaliação com julgamentos múltiplos | Claude | 4 (e 5, se houver) | 🔄 código pronto e testado; espera a anotação |
| 7 | Preparar o experimento de geração | Ambos | 1 | 🔄 31 de 120 respostas; limite diário do Groq |
| 8 | Anotar as respostas geradas | Vocês | 7 | nov–dez |
| 9 | Análise da geração e texto do capítulo | Claude | 8 | 🔄 código e metodologia (3.6) prontos; faltam resultados |
| 10 | Trabalhos Relacionados e referências | Ambos | — | ✅ 19/10 (vocês: ler o fichamento) |
| 11 | Figuras e capítulo de Desenvolvimento | Claude | 1 | ✅ 19/10 |
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
  - **PDF para o orientador:** `DOCUMENTO-ENVIO/TCC_RAG_UNESP_Bauru_rascunho_2026-10-19.pdf` (39 páginas, atualizado depois das etapas 3 a 11).
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

## Etapa 3 — Congelar o corpus 🔄 (parte técnica concluída em 19/10/2026)

- [ ] **Quem:** Ambos · **Depende de:** 1
- **Eu fiz (19/10):**
  - `scripts/snapshot_corpus.py` gera um pacote determinístico (mesmo hash em execuções repetidas): `dist/corpus-resolucoes-unesp-2016-2026.zip`, 2,4 MB, 939 arquivos (936 resoluções, `manifest.json`, `README.md` e `SHA256SUMS`);
  - **SHA-256 do pacote:** `91e825b6df098db1cacc60ee41f9f207cd5b8997de369f7ef68d014072aeafd6`;
  - somas de cada arquivo versionadas em `data/corpus_checksums.sha256`, e `python scripts/snapshot_corpus.py --verificar` confere qualquer cópia do corpus;
  - o hash e o período de coleta (02–08/06/2026) entram no texto, na seção 3.1;
  - o `eval_set.json` **ficou fora** do pacote de propósito: ele vai mudar nas Etapas 5 e 6 e será publicado à parte, quando estiver final.
- **Vocês fazem:**
  - escolher onde publicar (GitHub Release ou Zenodo, que dá DOI) e fazer o envio de `dist/corpus-resolucoes-unesp-2016-2026.zip` (o arquivo é gerado localmente e não vai para o git);
  - depois, me passar o link para eu registrá-lo no README e no texto.
- **Pronto quando:** o pacote estiver publicado e o link constar no README e no texto.

## Etapa 4 — Planilhas de julgamento de relevância (*pooling*) 🔄 (planilhas prontas em 19/10/2026)

- [ ] **Quem:** Ambos · **Depende de:** 1
- **Eu fiz (19/10):**
  - `scripts/pooling.py`: para cada uma das 50 consultas, junta os 5 primeiros documentos dos 4 métodos e a referência atual: **626 linhas por anotador** (7 a 20 documentos por consulta, média de 12,5);
  - `data/julgamentos/julgamento_matheus.xlsx` e `julgamento_rafael.xlsx`: o método não aparece, a ordem é embaralhada de forma diferente em cada uma, a coluna de nota só aceita 0/1/2 e há link oficial para cada resolução;
  - `data/julgamentos/GUIA_ANOTACAO.md`: critérios (0/1/2), exemplos e regras;
  - `data/julgamentos/pool.json` guarda qual método trouxe cada documento (**não abrir antes de anotar**);
  - o script **se recusa a sobrescrever** planilhas que já têm notas.
- **Vocês fazem:** ler o guia e anotar **separadamente, sem conversar**. Estimativa: 3 a 4 horas cada, em duas ou três sessões. Se for pesado demais, posso gerar uma versão mais curta (`--prof 3`).
- **Pronto quando:** as duas planilhas estiverem preenchidas em `data/julgamentos/`.

## Etapa 5 — Coleta de perguntas reais de alunos 🔄 (texto do formulário pronto em 19/10/2026)

- [ ] **Quem:** Ambos · **Depende de:** 2 (resposta sobre CEP)
- **Eu fiz (19/10):** `data/perguntas_reais/FORMULARIO.md`: título, texto de apresentação (anônimo, sem dados pessoais), campos e mensagem final. Lembrar de desligar "Coletar e-mails" e "Limitar a 1 resposta" no Google Forms, pois ambos identificariam a pessoa.
- **Vocês fazem:**
  - esperar a resposta do orientador sobre o **CEP** (pergunta 3 da mensagem);
  - criar o formulário, divulgar (turmas, centro acadêmico, biblioteca) e juntar **30 ou mais perguntas**;
  - exportar o CSV e colocá-lo em `data/perguntas_reais/respostas_forms.csv`.
- **Eu faço depois:** remover duplicatas e respostas com dado pessoal, descartar o que estiver fora do escopo, acrescentar as perguntas ao `eval_set.json` (tipo `real`) e gerar as planilhas de julgamento só para elas.
- **Pronto quando:** houver 80–100 consultas com julgamentos.
- **Se não der tempo ou não for autorizado:** seguir só com as 50 consultas atuais e declarar isso como limitação.

## Etapa 6 — Reavaliação com julgamentos múltiplos 🔄 (código pronto em 19/10/2026)

- [ ] **Quem:** Claude · **Depende de:** 4 (e 5, se houver)
- **Eu fiz (19/10):** `scripts/avaliar_julgamentos.py`:
  - lê as duas planilhas e calcula a concordância (simples, kappa de Cohen, kappa ponderado);
  - gera `divergencias.csv` com a coluna `nota_final` para vocês decidirem cada divergência (recusa rodar sem isso; `--permitir-divergencias` dá um resultado provisório);
  - calcula nDCG@5, Precision@5, Recall@5, Hit@K e MRR com vários documentos relevantes, comparações pareadas com Holm e IC por *bootstrap*, geral e por tipo de consulta;
  - **testado com julgamentos sintéticos** (nada disso entra no TCC); o `kappa` reproduz o exemplo clássico (0,4).
- **Eu faço quando houver anotação:** rodar, regenerar o documento, descrever o *pooling* e o kappa nos caps. 3 e 4, trocar as tabelas, atualizar resumo e conclusões e criar a tag `avaliacao-v3`.
- **Pronto quando:** o documento estiver regenerado com os resultados v3 e o texto coerente com eles.

## Etapa 7 — Preparar o experimento de geração 🔄 (infraestrutura pronta; geração em andamento)

- [ ] **Quem:** Ambos · **Depende de:** 1
- **Eu fiz (19/10):**
  - `scripts/montar_perguntas_geracao.py` → `data/geracao/perguntas.json`: **40 perguntas** (24 semânticas do conjunto de avaliação + 6 novas respondíveis, com a resposta de referência extraída do artigo + **10 sem resposta**: 5 sem nenhuma ocorrência no corpus e 5 "quase respondíveis"). A lista completa está no Apêndice B do TCC;
  - `scripts/gerar_respostas.py`: 3 condições (sem recuperação, RAG vetorial, RAG híbrido), resumível, espaçado pelo limite por minuto, grava resposta, trechos usados, tokens e latência;
  - `scripts/preparar_anotacao_geracao.py`: planilhas às cegas (condição oculta, ordem embaralhada por anotador, listas de valores válidos, trava contra sobrescrever) e `GUIA_ANOTACAO_GERACAO.md`;
  - piloto, ajuste dos prompts (v2) e troca do modelo: ver "Decisões que tomei" acima.
- **Situação da geração (19/10, 22h):** **31 de 120 respostas** feitas com o prompt v2 (g01 a g10 completas). Parou no **limite diário do plano gratuito do Groq: 200 mil tokens/dia** para o `gpt-oss-120b` (a maior parte foi gasta no piloto descartado). O limite se recarrega aos poucos (~139 tokens/min) e cada resposta com recuperação custa ~3,4 mil tokens, então as 89 restantes levam **cerca de 29 horas**.
- **O que está rodando:** deixei `python scripts/gerar_respostas.py` em segundo plano, esperando a recarga (ele retoma de onde parou; se a sessão fechar, é só rodar de novo).
- **Vocês fazem:**
  - **decidir como terminar a geração:** (a) deixar o computador ligado ~1 dia e rodar o script (de graça); ou (b) ativar o **Dev Tier** pago por uso em console.groq.com/settings/billing (só vocês podem fazer isso; este experimento inteiro usa ~300 mil tokens, o que custa centavos de dólar e acaba em minutos);
  - evitar usar a interface (que consome a mesma cota) enquanto a geração roda;
  - **confirmar as 10 perguntas "sem resposta"** (Apêndice B): nenhuma deve ter resposta nas resoluções.
- **Pronto quando:** as 120 respostas existirem e as planilhas de anotação estiverem geradas em `data/geracao/` (`python scripts/preparar_anotacao_geracao.py`).

## Etapa 8 — Anotar as respostas geradas

- [ ] **Quem:** Vocês · **Depende de:** 7
- **Vocês fazem:**
  - os dois anotam as cerca de 120 respostas (40 perguntas × 3 condições) **separadamente**, seguindo o guia;
  - estimativa: 2 a 3 horas por pessoa.
- **Eu faço:** tiro dúvidas sobre os critérios durante a anotação, se precisarem.
- **Pronto quando:** as duas planilhas estiverem preenchidas.

## Etapa 9 — Análise da geração e texto do capítulo 🔄 (código e metodologia prontos em 19/10/2026)

- [ ] **Quem:** Claude · **Depende de:** 8
- **Eu fiz (19/10):**
  - `scripts/analisar_geracao.py`: kappa por critério, divergências em `divergencias_geracao.csv` (coluna `valor_final`), correção, alucinação, citação, recusa, latência e tokens por condição, comparações pareadas (aleatorização para a correção; binomial exato para alucinação e recusa) com Holm. **Testado com anotações sintéticas**, o que revelou e corrigiu dois defeitos;
  - **seção 3.6 do TCC** (protocolo): 40 perguntas, 3 condições, anotação cega, critérios, definição de alucinação, testes e a limitação da cegueira parcial.
- **Eu faço quando houver anotação:** rodar a análise, acrescentar as tabelas ao documento, escrever resultados e discussão, atualizar resumo, abstract e considerações finais (objetivo f).
- **Pronto quando:** o documento estiver regenerado com os resultados da geração.

## Etapa 10 — Trabalhos Relacionados e referências ✅ (19/10/2026)

- [x] **Quem:** Ambos · **Depende de:** —
- **Feito:**
  - **seção 2.7** (o capítulo 2 virou "Referencial Teórico e Trabalhos Relacionados", sem renumerar o resto): recuperação densa × lexical × híbrida, português e domínio jurídico brasileiro, RAG para atendimento acadêmico, avaliação de RAG e alucinações, posicionamento do trabalho;
  - **12 referências novas**, todas conferidas em fonte primária (Crossref, ACL Anthology, arXiv, SBC); o total é **25**, todas citadas no texto, em ordem alfabética (o `validar_documento.py` confere isso);
  - `DOCUMENTO-ENVIO/fichamento_trabalhos_relacionados.md`: o que o TCC afirma de cada trabalho, por que importa, onde ler e perguntas prováveis da banca.
- **Vocês fazem:** **ler o fichamento e pelo menos o resumo de cada trabalho** (a banca pergunta). Três são de 2026 e só consegui ver a página de resumo, então leiam o texto completo antes de discuti-los.

## Etapa 11 — Figuras e capítulo de Desenvolvimento ✅ (19/10/2026)

- [x] **Quem:** Claude · **Depende de:** 1
- **Feito (o "capítulo de Desenvolvimento" ficou dentro do Cap. 3, para não renumerar o texto):**
  - **Figura 1** (arquitetura), **Figura 2** (resoluções por ano e distribuição do tamanho) e **Figura 3** (interface), todas com "Fonte:" e citadas no texto; geradas por `scripts/gerar_figuras.py` e `scripts/capturar_interface.py`;
  - **Quadro 1** (componentes e arquivos) e **Quadro 2** (prompts do sistema, lidos do código);
  - **Apêndice A** (50 consultas da avaliação) e **Apêndice B** (40 perguntas da geração), gerados dos JSON;
  - a Figura 3 mostra uma resposta cujo conteúdo conferi no texto da norma; uma captura anterior foi descartada por trazer um detalhe que a resolução não contém;
  - interface: renderiza o markdown das respostas e ganhou os acentos que faltavam.

## Etapa 12 — Formatação final no modelo BSI

> **Já adiantado em 19/10:** lista de abreviaturas e siglas (só as usadas, conferido pelo validador), siglas por extenso na primeira menção, apêndices e legendas com "Fonte:". **Falta:** decisão do orientador sobre o modelo Word oficial, ficha catalográfica, nomes da banca, ano 2027 na capa e (opcional) listas de ilustrações e de tabelas.

- [ ] **Quem:** Ambos · **Depende de:** 2 (decisão do formato), 6, 9, 10, 11
- **Eu faço:**
  - se o orientador exigir o modelo Word oficial, migrar o conteúdo para ele;
  - em qualquer caso: listas de tabelas, figuras e siglas; apêndices (conjunto de avaliação, prompt, exemplos de respostas); **ano da capa = 2027**; nomes da banca; cronograma "realizado";
  - conferir margens, espaçamento, legendas e citações ABNT.
- **Vocês fazem:** gerar a **ficha catalográfica** em biblioteca.unesp.br/ficha. Ela precisa dos dados de vocês e do número de páginas final.
- **Pronto quando:** o documento estiver completo no formato exigido.

## Etapa 13 — Revisão final e versão para o orientador

> **Ferramenta pronta:** `python scripts/validar_documento.py` repete a validação texto × dados × código (números dos resultados, hash do corpus, modelos e parâmetros, caminhos de arquivos citados, referências citadas, legendas, numeração, siglas). Já apontou, por exemplo, duas tabelas que nunca eram citadas no texto. Rodar antes de qualquer envio.

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
