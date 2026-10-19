# Rascunho de mensagem ao orientador (19/10/2026)

**Para:** Prof. Dr. Clayton Reginaldo Pereira
**Anexo:** `TCC_RAG_UNESP_Bauru_rascunho_2026-10-19.pdf` (25 páginas)
**Assunto:** TCC — versão revisada e dúvidas sobre a entrega de fevereiro

---

Prezado Prof. Clayton,

Tudo bem? Com a greve e o novo calendário, a entrega do nosso TCC passou para fevereiro de 2027. Aproveitamos o tempo para revisar o que já tínhamos e enviamos em anexo a versão atual do texto.

**Principais mudanças desde o TCC I**

- **Revisão da avaliação da recuperação.** Ao conferir o texto com o código, vimos que a nossa linha de base "BM25" usava, na verdade, o ranqueamento nativo do PostgreSQL (`ts_rank_cd`), e exigia que todos os termos da consulta aparecessem no mesmo trecho. Implementamos o BM25 de fato, corrigimos a busca por texto, passamos a medir a latência depois do aquecimento do modelo e incluímos testes de significância estatística.
- **Resultado.** A busca híbrida (RRF) continua com o melhor desempenho (MRR 0,785, contra 0,718 do BM25 e 0,690 da busca vetorial), mas, com 50 consultas, a diferença não é estatisticamente significativa no conjunto completo. Nas consultas semânticas ela é (p ajustado < 0,05). Reescrevemos os capítulos 4 e 5 e a discussão de acordo, com uma seção de limitações.
- **Escopo.** O corpus são as 936 resoluções gerais da UNESP (2016–2026); deixamos isso explícito no texto.

**Próximos passos (a partir de novembro)**

Ampliar o conjunto de avaliação (relevância julgada por dois anotadores e perguntas reais de alunos), avaliar a qualidade das respostas geradas pelo modelo de linguagem e escrever o TCC II.

**Gostaríamos de confirmar com o senhor**

1. A data de entrega/depósito e a data da banca em fevereiro, e quem comporá a banca.
2. Se a versão final deve seguir o modelo Word oficial do BSI ou se podemos manter o documento atual, que já segue as margens, a fonte e o espaçamento do modelo.
3. Se coletar perguntas anônimas de estudantes (formulário sem dados pessoais) exige submissão ao CEP.
4. Se mantemos o título "… da UNESP Bauru", apesar de o corpus ser de resoluções gerais da UNESP, ou se ajustamos para "… da UNESP".
5. Qualquer retorno que o senhor tenha sobre a versão do TCC I.

Obrigado,
Matheus e Rafael
