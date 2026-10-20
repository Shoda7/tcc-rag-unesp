# Guia de anotação — respostas geradas pelo sistema (Etapa 8)

**Objetivo:** avaliar a qualidade das respostas que o modelo de linguagem gerou em três situações, **sem saber qual
situação produziu cada resposta**:

| Condição | O que o modelo recebeu |
|---|---|
| Sem recuperação | só a pergunta (usa o conhecimento do próprio modelo) |
| RAG vetorial | a pergunta + os 5 trechos mais próximos pela busca vetorial |
| RAG híbrido | a pergunta + os 5 trechos do híbrido (vetorial + BM25) |

**Arquivos:** `anotacao_matheus.xlsx` e `anotacao_rafael.xlsx` (cada um faz o seu), com **120 linhas**
(40 perguntas × 3 respostas). Estimativa: 2 a 3 horas.

## Os dois tipos de pergunta

- **Respondível (30):** a resposta está no corpus. A coluna **Referência** traz a resposta esperada (nas perguntas novas) ou o
  documento de referência com o trecho mais próximo (nas demais). Se tiver dúvida, abra o link oficial.
- **SEM resposta no corpus (10):** não há resposta nas resoluções; o certo é o sistema **dizer que não encontrou**. Metade
  são assuntos que nem aparecem no corpus; a outra metade são "quase respondíveis" (o tema aparece, mas o dado pedido, não).

## Critérios (colunas H a K)

**H — Correção** (só perguntas respondíveis; nas SEM resposta, marque **N/A**)

| Nota | Quando |
|---|---|
| **2** | Resposta correta e completa em relação à referência. |
| **1** | Parcialmente correta: incompleta, ou com imprecisão que não muda a conclusão. |
| **0** | Errada, não responde, ou **recusa sem motivo** ("não encontrei" quando a resposta existia). |

**I — Alucinação (Sim/Não)** — vale para **todas** as perguntas.
Marque **Sim** se a resposta traz uma afirmação específica (número, data, prazo, artigo, nome de documento, procedimento) que
**não está nas resoluções do corpus** ou que as **contradiz**. Conhecimento geral correto, mas que não consta nas resoluções,
também é **Sim** aqui: o que medimos é a **fidelidade ao corpus**, não a veracidade no mundo. Respostas que só dizem "não sei /
não encontrei" são **Não**.

**J — Citação correta (Sim/Não/N/A)**
A coluna F lista as resoluções que a resposta menciona (por nome de arquivo ou em prosa). Marque **Sim** se, em cada citação, o
documento citado realmente traz a informação afirmada; **Não** se alguma citação estiver errada (documento inexistente, ou que
não diz aquilo); **N/A** se a resposta não cita nenhuma resolução.

**K — Recusa adequada (Sim/Não/N/A)** (só perguntas SEM resposta; nas respondíveis, **N/A**)
**Sim** = disse que não encontrou / não sabe e **não inventou** a informação pedida. **Não** = inventou ou "chutou" a resposta.
Se recusou mas ainda assim acrescentou informação inventada, marque **Não** e explique na coluna L.

## Regras

1. **Anote sozinho(a)**, sem conversar com a outra pessoa e **sem tentar adivinhar a condição** de cada resposta. (Respostas sem
   recuperação costumam não citar resoluções, então às vezes dá para desconfiar; ignore isso ao julgar.)
2. Julgue **o conteúdo**, não o estilo: tamanho, formatação e tom não contam.
3. Confira **cada** número, data e artigo importante contra a referência ou o link oficial. Uma data errada em uma resposta
   longa e bem escrita continua sendo **alucinação**.
4. **Documentos substituídos:** se a resposta é verdadeira para uma versão antiga da norma, mas a pergunta pede a regra do ano
   indicado (ex.: calendário de 2020), julgue em relação ao documento do ano pedido.
5. Dúvida entre duas notas: dê a melhor estimativa e escreva "?" na coluna L; revemos juntos no fim.
6. **Não altere** as colunas A–G nem a ordem das linhas e salve a cada pergunta. **Não preencha em branco**: toda linha
   respondível tem H, I e J; toda linha SEM resposta tem H = N/A, I, J e K.

## Depois de anotar

- Coloquem o arquivo preenchido em `data/geracao/` (mesmo nome).
- **Não abram** `chave_condicoes.json` nem **rodem de novo** `scripts/preparar_anotacao_geracao.py` (ele recusa sobrescrever
  planilhas já anotadas, mas a chave quebra o julgamento às cegas).
- Eu calculo a concordância entre vocês (kappa de Cohen; ponderado na Correção) e listo as divergências para decidirem juntos.

## Observações metodológicas (para o texto do TCC)

- Condição oculta e ordem das respostas embaralhada por pergunta e por anotador; identificadores anônimos.
- A cegueira é parcial: respostas sem recuperação raramente citam resoluções. Isso entra como limitação.
- 40 perguntas × 3 condições = 120 respostas; modelo `openai/gpt-oss-120b` (Groq), temperatura 0,1, raciocínio médio,
  5 trechos de contexto por pergunta nas condições com recuperação.
