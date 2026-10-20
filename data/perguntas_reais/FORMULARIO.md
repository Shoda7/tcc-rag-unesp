# Formulário de perguntas reais (Etapa 5)

> **Antes de divulgar:** confirmar com o orientador se a coleta exige submissão ao CEP (pergunta 3 da mensagem
> ao Prof. Clayton). O formulário abaixo é anônimo e não coleta nenhum dado pessoal, mas essa decisão é dele/do comitê.
> Criar no Google Forms com **"Coletar endereços de e-mail" DESLIGADO** e **"Limitar a 1 resposta" DESLIGADO**
> (os dois exigem login e identificariam a pessoa).

## Título
Dúvidas sobre as regras da UNESP — pesquisa de TCC

## Texto de apresentação
Somos Matheus e Rafael, estudantes de Sistemas de Informação da UNESP Bauru. Estamos desenvolvendo um assistente
que responde dúvidas sobre as resoluções da UNESP (regras de graduação, pós-graduação, bolsas, extensão,
calendário, diplomas etc.) e precisamos de **perguntas reais** para avaliar se ele funciona.

Você vai escrever de **1 a 3 dúvidas** que já teve, ou que teria, sobre as regras da universidade, **do jeito que
perguntaria a um colega ou à secretaria**. Leva menos de 3 minutos.

- A participação é voluntária e **anônima**: não pedimos nome, e-mail, RA nem qualquer dado pessoal.
- **Não escreva dados pessoais** nas perguntas (nome, RA, CPF, telefone, e-mail). Se escrever, descartaremos a resposta.
- As perguntas serão usadas só para avaliar o sistema no TCC e poderão ser reproduzidas (sem identificação) no trabalho.
- **Não consulte** as resoluções nem o site para escrever: queremos a dúvida como ela surge.

## Campos
1. **Sua dúvida** (resposta longa, obrigatória) — "Escreva uma dúvida sobre as regras da UNESP."
2. **Outra dúvida** (resposta longa, opcional).
3. **Mais uma dúvida** (resposta longa, opcional).
4. **Você é...** (múltipla escolha, opcional): Estudante de graduação · Estudante de pós-graduação · Docente · Servidor(a) técnico-administrativo(a) · Outro.
5. **Você já precisou consultar uma resolução da UNESP?** (múltipla escolha, opcional): Sim · Não.

## Mensagem de agradecimento (após envio)
Obrigado! Se quiser conhecer o resultado, procure o TCC "Sistema RAG para documentos regulatórios da UNESP" na
biblioteca da UNESP Bauru (previsto para fevereiro de 2027).

## Meta e como divulgar
- **Meta: 30 ou mais perguntas utilizáveis** (de umas 15 a 20 pessoas já bastam).
- Divulgar em grupos de turma, centro acadêmico e biblioteca. Prazo sugerido: 2 semanas.

## O que eu faço depois (quando houver respostas)
Exporte as respostas em CSV (Respostas → "Vincular ao Sheets" → Arquivo → Baixar como CSV) e coloque em
`data/perguntas_reais/respostas_forms.csv`. Eu então: removo duplicatas e respostas com dado pessoal, descarto o que
estiver fora do escopo das resoluções, acrescento as perguntas ao `data/eval_set.json` (tipo `real`) e gero as
planilhas de julgamento só para elas (mesmo guia da Etapa 4).
