# Guia de anotação — relevância dos documentos (Etapa 4)

**Objetivo:** dizer, para cada consulta, quais documentos do corpus realmente ajudam a respondê-la. Essas
anotações substituem a "resposta única" que usamos até agora e permitem medir os métodos de busca com mais
de um documento correto por consulta (nDCG@5 e Recall@5).

**Arquivos:** `julgamento_matheus.xlsx` e `julgamento_rafael.xlsx`. Cada um faz a **sua** planilha.
São **626 linhas** (50 consultas, de 7 a 20 documentos cada). Estimativa: de 3 a 4 horas, em duas ou três sessões.

## O que fazer

Na aba **Julgamentos**, preencha a coluna **F** (amarela) com:

| Nota | Significado | Exemplo |
|---|---|---|
| **2** | O documento **responde** à consulta: a informação principal está nele. | Consulta "reingresso de alunos nos cursos de graduação"; o documento é a resolução que regulamenta o reingresso. |
| **1** | O documento trata do tema e traz informação útil, mas **não responde por completo**, ou só responde de passagem. | Resolução de calendário escolar que cita o prazo de reingresso em um artigo. |
| **0** | O documento **não ajuda** a responder. | Resolução de pós-graduação para uma pergunta sobre graduação. |

## Regras

1. **Julgue o documento inteiro, não só o trecho.** O trecho mostrado é o que o sistema encontrou, mas a resposta pode estar em outra parte. Em caso de dúvida, abra o **link oficial** (coluna H).
2. **Anote sozinho(a)**, sem conversar com a outra pessoa e sem tentar descobrir qual sistema trouxe cada documento (a planilha não mostra isso de propósito).
3. **Cada documento é julgado de forma independente.** Pode haver vários documentos com nota 2 na mesma consulta, ou nenhum.
4. **Versão antiga de uma norma:** se o documento foi substituído ou revogado por outro, mas ainda trata do tema, dê **1** e escreva "versão antiga" na coluna G. Não dê 2 só porque o texto responde a pergunta que valia em outra época.
5. **Consulta ambígua:** julgue pelo sentido mais provável de quem perguntou. Se mais de uma leitura for razoável, anote na coluna G.
6. **Não altere** as colunas A–E nem a ordem das linhas, e **salve a cada consulta**.
7. **Não deixe linhas em branco.** Se estiver em dúvida entre duas notas, dê a sua melhor estimativa e escreva "?" na coluna G; revemos essas dúvidas juntos no fim.

## Depois de anotar

- Cada um coloca o arquivo preenchido em `data/julgamentos/` (mesmo nome). Se anotarem em computadores diferentes, copiem só o próprio arquivo e me enviem depois.
- **Não rodem `scripts/pooling.py` de novo**: ele gera planilhas novas e apagaria o trabalho. (O script se recusa a sobrescrever planilhas que já têm notas.)
- **Não** comparem as planilhas antes de terminarem. Eu calculo a concordância entre vocês (kappa de Cohen) e listo as divergências para uma conversa curta; a decisão final de cada divergência fica registrada.
- O arquivo `pool.json` guarda qual método trouxe cada documento. **Não abram antes de terminar**: ele quebra o julgamento às cegas.

## Observações metodológicas (para o texto do TCC)

- *Pooling*: o conjunto a julgar é a união dos 5 primeiros documentos de cada um dos 4 métodos (vetorial, FTS-PG, BM25 e híbrido), mais a resolução que usávamos como referência. Documentos que nenhum método trouxe ficam sem julgamento e contam como irrelevantes (suposição padrão do *pooling*).
- Ordem das linhas embaralhada e diferente para cada anotador, para evitar viés de posição.
- Escala graduada (0/1/2) e concordância medida por kappa de Cohen (ponderado, por ser uma escala ordinal).
