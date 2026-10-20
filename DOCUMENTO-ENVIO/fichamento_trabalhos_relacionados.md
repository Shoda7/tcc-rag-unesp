# Fichamento dos trabalhos relacionados (seção 2.7 do TCC)

> Para **ler antes da banca**: a banca costuma perguntar sobre os trabalhos citados. Para cada um: o que o TCC afirma sobre ele,
> por que ele importa para o nosso trabalho e onde ler. Os dados bibliográficos foram conferidos em fonte primária em
> 19/10/2026. O resumo de cada trabalho é só o que o texto do TCC usa; **leiam pelo menos o resumo (abstract) original**.
>
> Três dos trabalhos são de 2026 (Bessa et al. no PROPOR; Sousa e Soares e Santos et al. no SBIE): eu só tive acesso à
> página de resumo deles, então vale ler o texto completo antes de qualquer discussão mais detalhada com a banca.

## Recuperação densa, lexical e híbrida

| Trabalho | O que o TCC diz | Por que importa para nós |
|---|---|---|
| **Karpukhin et al. (2020)** — *Dense Passage Retrieval for Open-Domain Question Answering*. EMNLP 2020, p. 6769–6781. [DOI 10.18653/v1/2020.emnlp-main.550](https://doi.org/10.18653/v1/2020.emnlp-main.550) | A recuperação densa por duplo codificador superava o BM25 em perguntas de domínio aberto. | Origem da ideia de usar embeddings no lugar de palavras-chave; é o que a nossa busca vetorial faz. |
| **Thakur et al. (2021)** — *BEIR: a Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models*. NeurIPS 2021 (Datasets and Benchmarks). [arXiv:2104.08663](https://arxiv.org/abs/2104.08663) | Em dados de vários domínios, sem ajuste, o BM25 continua uma linha de base robusta e vence modelos densos em vários conjuntos. | Explica por que o BM25 empatou com a busca vetorial no nosso corpus. |
| **Lin (2019)** — *The Neural Hype and Comparisons Against Weak Baselines*. ACM SIGIR Forum 52(2), p. 40–51. [DOI 10.1145/3308774.3308781](https://doi.org/10.1145/3308774.3308781) | Critica artigos que mostram ganhos de modelos neurais contra linhas de base fracas ou mal ajustadas. | **É o nosso caso na versão preliminar:** a "linha de base BM25" era o `ts_rank_cd` com E obrigatório. Tragam este exemplo se a banca perguntar o que mudou. |
| **Rosa et al. (2021)** — *Yes, BM25 is a Strong Baseline for Legal Case Retrieval*. [arXiv:2105.05686](https://arxiv.org/abs/2105.05686) | Um BM25 simples ficou em 2º lugar na tarefa de recuperação de casos do COLIEE 2021. | BM25 é forte em texto jurídico/normativo, como as resoluções. |
| **Cormack et al. (2009)** — *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods*. SIGIR 2009, p. 758–759. | O RRF combina rankings sem calibração (já estava no TCC). | É o método do nosso "híbrido". |

## Português e domínio jurídico brasileiro

| Trabalho | O que o TCC diz | Por que importa para nós |
|---|---|---|
| **Bonifacio et al. (2021)** — *mMARCO: a Multilingual Version of the MS MARCO Passage Ranking Dataset*. [arXiv:2108.13897](https://arxiv.org/abs/2108.13897) | Versão multilíngue do MS MARCO (traduzida), com português. | Recurso de avaliação em português, mas com texto geral, não normativo. |
| **Bueno et al. (2024)** — *Quati: a Brazilian Portuguese Information Retrieval Dataset from Native Speakers*. [arXiv:2404.06976](https://arxiv.org/abs/2404.06976) (também no STIL 2024) | Consultas escritas por falantes nativos; relevância julgada com apoio de um LLM. | Mostra a prática de usar consultas de falantes reais, que é o que a Etapa 5 faz. Citamos a versão arXiv porque a ordem dos autores difere do Anthology. |
| **Bessa, Lobato e Junior (2026)** — *Development and Evaluation of a Hybrid Information Retrieval System Applied to the Brazilian Legal Domain*. PROPOR 2026, v. 2, p. 186–190. [Anthology](https://aclanthology.org/2026.propor-2.26/) | Sistema híbrido (BM25L + modelo de linguagem) para o direito brasileiro. | Converge com a nossa escolha de combinar sinal lexical e semântico. **Só vimos o resumo.** |

## RAG para atendimento acadêmico

| Trabalho | O que o TCC diz | Por que importa para nós |
|---|---|---|
| **Sousa e Soares (2026)** — *RAG para Atendimento Acadêmico: uma Avaliação de Modelos de Embedding Compactos no Contexto Universitário*. SBIE 2026, p. 1701–1716. [DOI 10.5753/sbie.2026.28059](https://doi.org/10.5753/sbie.2026.28059) | Compara embeddings compactos de código aberto (até 0,6 bi de parâmetros) com proprietários, com Recall, MRR e nDCG; os compactos são competitivos. | Valida a escolha do e5-small (modelo compacto, local). **O trabalho mais próximo do nosso.** |
| **Santos et al. (2026)** — *LIA: um Chatbot para Consulta de Diretrizes de Inteligência Artificial em Universidades Brasileiras*. SBIE 2026, p. 487–502. [DOI 10.5753/sbie.2026.27205](https://doi.org/10.5753/sbie.2026.27205) | RAG com ChromaDB + BM25 + reranqueador (BAAI). | Também usa recuperação híbrida; tem reranqueamento, que nós deixamos como trabalho futuro. |

## Avaliação de RAG e alucinações

| Trabalho | O que o TCC diz | Por que importa para nós |
|---|---|---|
| **Es et al. (2024)** — *RAGAs: Automated Evaluation of Retrieval Augmented Generation*. EACL 2024 (demos), p. 150–158. [DOI 10.18653/v1/2024.eacl-demo.16](https://doi.org/10.18653/v1/2024.eacl-demo.16) | Avalia RAG sem respostas de referência (por exemplo, fidelidade ao contexto). | Alternativa automática à nossa anotação humana; dá para citar como trabalho futuro. |
| **Magesh et al. (2025)** — *Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools*. J. Empirical Legal Studies 22(2), p. 216–242. [DOI 10.1111/jels.12413](https://doi.org/10.1111/jels.12413) | Ferramentas comerciais jurídicas com recuperação ainda alucinam em parte das respostas (avaliação pré-registrada, 200+ consultas). | Justifica avaliar a **fidelidade** das respostas, e não só a recuperação. |
| **Dahl et al. (2024)** — *Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models*. J. Legal Analysis 16(1), p. 64–93. [DOI 10.1093/jla/laae003](https://doi.org/10.1093/jla/laae003) | Taxas altas de alucinação em consultas jurídicas e uma tipologia dos erros. | Base para a nossa definição de alucinação (afirmação específica não suportada pelo corpus). |

## Perguntas que a banca pode fazer sobre esta seção

1. **"Por que não comparar com um LLM maior / com reranqueamento?"** Fora do escopo; está em trabalhos futuros, e o LIA usa reranqueador.
2. **"O que o seu trabalho tem de novo em relação ao Sousa e Soares (2026)?"** Comparamos quatro métodos de recuperação (inclusive a busca nativa do PostgreSQL × BM25 real) com testes de significância, sobre resoluções da UNESP, e avaliamos a geração com anotação humana às cegas. Eles comparam modelos de embedding.
3. **"Por que a versão preliminar mostrava o FTS tão fraco?"** Erro de implementação nosso (E obrigatório e `ts_rank_cd`); é exatamente o alerta de Lin (2019).
4. **"Como vocês definem alucinação?"** Afirmação específica (número, data, artigo, procedimento) que não está nas resoluções do corpus ou que as contradiz (fidelidade ao corpus), seguindo a ideia de Dahl et al. (2024) e Magesh et al. (2025).
