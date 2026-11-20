# Roteiro da apresentação para a banca (rascunho)

> **Estado (19/10/2026):** estrutura, tempos, demonstração e perguntas prováveis. Os números marcados com
> `[ETAPA n]` só existem depois que essa etapa terminar; os demais já vêm de `data/resultados_resumo.json`.
> Versão para **20 minutos** de fala; ajustar quando o orientador informar o tempo da banca (Etapa 2).
> Os slides em si ficam para depois da Etapa 13, quando o texto e os resultados estiverem fechados.

## 1. Slides, tempo e conteúdo

| # | Slide | Tempo | O que mostrar / dizer | Fonte no TCC |
|---|---|---|---|---|
| 1 | Título | 0:30 | Título, autores, orientador, UNESP Bauru, fev/2027 | capa |
| 2 | Problema | 1:30 | Resoluções espalhadas em um portal; aluno e biblioteca não sabem qual vale. 936 resoluções (2016–2026) | 1.1 |
| 3 | Objetivo e perguntas | 1:00 | (1) qual método de busca recupera melhor? (2) o RAG melhora a resposta do LLM? | 1.2 |
| 4 | Como funciona um RAG | 2:00 | Um diagrama só: pergunta → busca → trechos → LLM → resposta com fonte. Em uma frase cada: embedding, BM25, RRF | 2.2 a 2.5 |
| 5 | Trabalhos relacionados | 1:00 | BEIR e Rosa et al. (BM25 é uma linha de base forte); Quati e mMARCO (português); Santos et al. e Sousa e Soares (RAG universitário); lacuna: resoluções da UNESP e testes estatísticos | 2.7 |
| 6 | O corpus | 1:00 | Figura 2: resoluções por ano e tamanho dos documentos; hash SHA-256 do corpus | 3.1, Fig. 2 |
| 7 | Arquitetura | 1:30 | Figura 1: indexação e consulta; PostgreSQL + pgvector, e5-small local, FastAPI, React | cap. 3, Fig. 1 |
| 8 | Como avaliamos a recuperação | 1:30 | 50 consultas (26 lexicais, 24 semânticas), Hit@K e MRR, teste de aleatorização com correção de Holm. `[ETAPA 6]` julgamentos de dois anotadores, kappa, nDCG@5 | 3.5 |
| 9 | Resultados da recuperação | 2:00 | Tabela 1 como gráfico de barras com IC95%: RRF 0,785; BM25 0,718; vetorial 0,690; FTS-PG 0,439 | 4.2, Tab. 1 |
| 10 | Por tipo de consulta e significância | 1:30 | Nas semânticas o RRF (0,715) supera vetorial (0,518) e BM25 (0,524), com Holm < 0,05; nas lexicais não há diferença. BM25 × FTS-PG: p ajustado 0,0008 | 4.3 e 4.4, Tab. 2–3 |
| 11 | Latência e custo | 1:00 | BM25 6 ms, vetorial 104 ms, RRF 109 ms (mediana); custo zero (hardware local, Groq gratuito) | 4.5, Tab. 4 |
| 12 | Como avaliamos a geração | 1:30 | 40 perguntas (30 respondíveis, 10 sem resposta), 3 condições (sem recuperação, RAG vetorial, RAG híbrido), anotação cega pelos dois autores | 3.6 |
| 13 | Resultados da geração | 2:00 | `[ETAPA 9]` correção, alucinação, citação correta e recusa por condição, com testes | cap. 4 (a escrever, Etapa 9) |
| 14 | Demonstração | 2:30 | Ver seção 2 | — |
| 15 | Limitações | 1:00 | 50 consultas, relevância por documento único (mitigada em `[ETAPA 6]`), corpus congelado em jun/2026, e5-small trunca chunks longos, mas a ablação mostrou que isso não prejudica (pergunta 3.6 abaixo), LLM hospedado | 4.6, 4.7 |
| 16 | Conclusões e trabalhos futuros | 1:00 | Híbrido é o mais robusto, sobretudo nas perguntas semânticas; próximos passos: reranker, embeddings maiores, perguntas reais | cap. 5 |
| 17 | Perguntas | — | Slide com o resumo dos números principais | — |

Total: 21:30 (cortar o slide 5 ou unir 6 e 7 se a banca limitar a 20 min).

## 2. Roteiro da demonstração (2:30)

Preparar **antes**: Docker no ar (`tcc-pgvector` saudável), `.env` com `GROQ_API_KEY`, backend (`uvicorn app.main:app`) e frontend (`npm run dev`) rodando, uma consulta de aquecimento feita (o primeiro embedding demora) e o **vídeo de reserva** gravado (Etapa 14). A cota diária do Groq é de 200 mil tokens: **não rodar o experimento de geração no dia**.

1. **Pergunta com resposta nas resoluções** (30 s): "Posso usar ChatGPT e ferramentas de IA nos meus trabalhos acadêmicos na UNESP?" Mostrar a resposta com citação e abrir a fonte (a Resolução UNESP nº 13/2025 e seus artigos).
2. **Contraste com o modelo sozinho** (30 s): mesma pergunta na condição sem recuperação; a resposta é genérica ("depende do curso, disciplina e orientador"). Só mostrar se o pré-teste confirmar.
3. **Pergunta de procedimento** (30 s): "Como posso me transferir de outra universidade para a UNESP?" Mostrar as fontes recuperadas e que são resoluções de transferência.
4. **Pergunta sem resposta no corpus** (30 s): "Qual é o cardápio do restaurante universitário desta semana?" O sistema deve dizer que não encontrou. **Testar antes**; se o modelo inventar, usar outra (ex.: horário da biblioteca) e dizer isso na apresentação.
5. **Comparar métodos** (30 s, opcional): a mesma consulta semântica com os métodos `bm25` e `vector` da API, para ver a diferença nos trechos.

Plano B: se o Groq estiver fora do ar ou sem cota, mostrar só a busca (os trechos recuperados) e passar para o vídeo.

## 3. Perguntas prováveis da banca e respostas sugeridas

**3.1. Por que implementaram o BM25 em vez de usar o ranqueamento do PostgreSQL?**
O `ts_rank_cd` não é BM25: não usa IDF nem a normalização por tamanho do documento do BM25, e a versão do TCC I exigia todos os termos na consulta. Reimplementamos o BM25 (k₁ = 1,2; b = 0,75) sobre os mesmos lexemas do PostgreSQL. Com o mesmo pré-processamento, o BM25 ficou em MRR 0,718 contra 0,439 do FTS-PG (p ajustado = 0,0008): a função de ranqueamento pesa.

**3.2. O híbrido é mesmo melhor?**
No conjunto todo, a diferença do RRF para o vetorial e para o BM25 não é significativa depois da correção de Holm (p = 0,11 e 0,26), e dizemos isso no texto. Nas consultas semânticas é (p = 0,045 contra o vetorial e 0,025 contra o BM25). Nas lexicais não há diferença. Com 50 consultas, o poder do teste é baixo; é por isso que ampliamos o conjunto `[ETAPA 5/6]`.

**3.3. O conjunto de avaliação é viciado? Quem escreveu as perguntas?**
As 50 consultas foram escritas por nós, cada uma com um documento de referência, o que penaliza trechos de outros documentos que também respondem. Mitigamos com *pooling*: os resultados dos quatro métodos foram julgados por dois anotadores (0/1/2), com kappa e nDCG@5 `[ETAPA 6]`, e coletamos perguntas reais de estudantes `[ETAPA 5]`.

**3.4. O título diz "UNESP Bauru", mas o corpus é da UNESP inteira.**
As 936 resoluções são normas gerais, que valem para todos os câmpus, inclusive Bauru; o uso previsto é a biblioteca do câmpus. Normas locais (portarias da unidade) não estão no corpus, e isso é uma limitação. `[ajustar conforme a resposta do orientador, Etapa 2]`

**3.5. Por que o e5-small e não um modelo maior?**
Roda em CPU sem GPU, é gratuito e tem 384 dimensões; Sousa e Soares (2026) mostram que modelos compactos são competitivos em português. Testamos o efeito do tamanho do chunk e, se der tempo, embeddings maiores `[ETAPA X]`.

**3.6. Os chunks de 350 palavras não passam do limite do modelo?**
Passam: medimos 66% deles acima de 512 tokens (mediana de 541), então o vetor só representa o início do trecho; o BM25 e o FTS usam o texto todo. Reindexamos com chunks de 250 palavras (2,4% acima do limite) em um banco separado e comparamos (seção 4.6, Tabela 5): o chunk menor **não melhorou** nenhum método (vetorial 0,690 → 0,652; híbrido 0,785 → 0,752; BM25 0,718 → 0,720; nada significativo). Na mediana, a truncagem corta só 29 de 541 tokens (~5%), e o trecho truncado ainda tem mais texto que um chunk inteiro de 250 palavras; o chunk menor perde contexto, e as consultas semânticas foram as que mais caíram. Por isso mantivemos 350 palavras.

**3.7. Por que o gpt-oss-120b via Groq?**
O LLaMA 3.3 70B deixou de ser oferecido pelo Groq durante o trabalho; o gpt-oss-120b tem pesos abertos e o mesmo plano gratuito. Registramos modelo, parâmetros, prompts e todas as respostas no repositório, porque um modelo hospedado pode mudar.

**3.8. Como vocês mediram alucinação?**
Anotação cega pelos dois autores, com a pergunta, a resposta e os trechos recuperados, sem a condição: correção (0–2), alucinação (afirmação sem apoio nos trechos), citação correta, recusa. Concordância por kappa e testes exatos para comparar as condições `[ETAPA 9]`.

**3.9. O sistema se recusa quando não sabe?**
A recusa vem só do prompt ("se a informação não estiver nos trechos, diga que não encontrou"): não há limiar de similaridade. Medimos com 10 perguntas sem resposta no corpus `[ETAPA 9]`.

**3.10. E a LGPD?**
O corpus é público. As perguntas dos usuários são enviadas ao provedor do LLM (Groq, nos EUA); por isso a interface não deve pedir dados pessoais e o formulário de coleta é anônimo. `[a interface ainda não exibe aviso sobre dados pessoais: incluir antes da banca]`

**3.11. Quanto custa?**
R$ 0 no experimento: embeddings, banco e busca rodam localmente e o Groq usa o plano gratuito (limite de 200 mil tokens por dia, que atrasou o experimento de geração). Em produção, o custo seria o do provedor do LLM por consulta (cerca de 3,4 mil tokens por resposta RAG).

**3.12. O que acontece quando uma resolução é revogada ou alterada?**
O corpus está congelado (coleta de jun/2026, hash SHA-256 no texto) e não trata revogações. A coleta é incremental (`manifest.json`), mas a reindexação e a marcação de normas revogadas são trabalho futuro.

**3.13. Dá para reproduzir?**
Sim: corpus empacotado com hash, tag `avaliacao-v2`, sementes fixas, scripts que geram os JSON de onde saem as tabelas do texto, e repositório público (https://github.com/Shoda7/tcc-rag-unesp).

**3.14. Por que RRF com k = 60 e sem ajustar?**
É o valor padrão de Cormack et al. (2009). Não ajustamos para não sobreajustar a 50 consultas.

**3.15. Um aluno usaria isso? Fizeram teste de usabilidade?**
Não fizemos teste de usabilidade; a interface foi pensada para um quiosque de biblioteca. Coletamos perguntas reais de alunos para a avaliação `[ETAPA 5]`, mas a aceitação pelo usuário final fica como trabalho futuro.

**3.16. Por que não usar um reranker ou um LLM como juiz?**
Ficaram fora do escopo (custo e tempo). O reranqueamento com *cross-encoder* é a próxima ablação; para julgar relevância preferimos anotadores humanos e medir a concordância.
