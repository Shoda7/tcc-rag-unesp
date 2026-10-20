"""Monta o conjunto de perguntas do experimento de geracao (data/geracao/perguntas.json).

40 perguntas:
  - 24 respondiveis, as consultas "semanticas" do eval_set (ja escritas como pergunta);
  -  6 respondiveis NOVAS, sobre resolucoes que as 24 anteriores nao cobrem, com a resposta
     de referencia extraida do proprio texto da resolucao (artigo indicado);
  - 10 SEM resposta no corpus: o comportamento correto e dizer que nao encontrou. Cinco tratam de
     assuntos que nao aparecem em nenhuma resolucao (busca por palavra-chave: 0 ocorrencias) e cinco
     sao "quase respondiveis" (o tema aparece, mas o dado pedido nao), que testam se o modelo inventa.

Uso: python scripts/montar_perguntas_geracao.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "geracao" / "perguntas.json"

NOVAS = [
    {
        "pergunta": "Quais tipos de bolsa podem ser pagas com recursos de convênios e contratos da UNESP e quem pode recebê-las?",
        "fontes": ["resolucao_2019_0044.txt"],
        "resposta_referencia": "Bolsas de ensino, de pesquisa, de extensão e de pós-doutorado (Art. 2º). Podem receber as três primeiras "
                               "os alunos regulares de graduação, mestrado e doutorado que não recebam outra bolsa ou auxílio que exija "
                               "exclusividade (Art. 3º). Res. 44/2019.",
    },
    {
        "pergunta": "Até que data os alunos da graduação da UNESP podem renovar a matrícula para o ano letivo de 2020?",
        "fontes": ["resolucao_2019_0073.txt"],
        "resposta_referencia": "Até o limite máximo de 17 de janeiro de 2020 (Art. 3º, IX). Res. 73/2019.",
    },
    {
        "pergunta": "Até que data deve ser concluído o processo seletivo de transferência para o início do ano letivo de 2018 na graduação da UNESP?",
        "fontes": ["resolucao_2017_0076.txt"],
        "resposta_referencia": "Até o limite máximo de 23/02/2018 para o início de ano (20/07/2018 para o meio de ano) (Art. 3º, VII). Res. 76/2017.",
    },
    {
        "pergunta": "Quem pode se candidatar ao Vestibular Unesp Meio de Ano 2017?",
        "fontes": ["resolucao_2017_0027.txt"],
        "resposta_referencia": "Portador de certificado de conclusão do Ensino Médio ou equivalente, quem estiver cursando o Ensino Médio "
                               "ou equivalente, e portador de diploma de curso superior (Art. 2º). Res. 27/2017.",
    },
    {
        "pergunta": "Os diplomas de mestrado e doutorado da UNESP são emitidos em formato digital?",
        "fontes": ["resolucao_2024_0050.txt"],
        "resposta_referencia": "Sim: os diplomas dos concluintes de mestrado e doutorado dos programas stricto sensu passam a ser expedidos "
                               "e registrados em formato digital (Art. 1º). Res. 50/2024.",
    },
    {
        "pergunta": "Até que data as unidades da UNESP devem fixar o calendário escolar dos cursos de graduação para o ano letivo de 2017?",
        "fontes": ["resolucao_2016_0081.txt"],
        "resposta_referencia": "Até 28/11/2016, por Portaria do Diretor, com aprovação da Congregação e do Conselho Diretor (Art. 2º). Res. 81/2016.",
    },
]

SEM_RESPOSTA = [
    # assunto ausente do corpus (0 ocorrencias nas 936 resolucoes)
    ("Qual é o horário de funcionamento da biblioteca da Faculdade de Ciências de Bauru?", "sem_ocorrencia"),
    ("Como solicito autorização para estacionar meu carro no câmpus de Bauru?", "sem_ocorrencia"),
    ("Como me conecto à rede Wi-Fi eduroam nos câmpus da UNESP?", "sem_ocorrencia"),
    ("Qual linha de ônibus passa na frente da Faculdade de Ciências de Bauru?", "sem_ocorrencia"),
    ("Quais são os horários de funcionamento da piscina e das quadras esportivas da UNESP de Bauru?", "sem_ocorrencia"),
    # tema aparece no corpus, mas o dado pedido nao (testa invencao)
    ("Qual é o cardápio do restaurante universitário desta semana?", "quase_respondivel"),
    ("Qual é o valor atual da bolsa de iniciação científica da Fapesp?", "quase_respondivel"),
    ("Qual é o salário de um professor assistente doutor da UNESP em 2026?", "quase_respondivel"),
    ("Qual foi a nota de corte do curso de Sistemas de Informação de Bauru no vestibular de 2026?", "quase_respondivel"),
    ("Quando será a próxima colação de grau dos formandos de Sistemas de Informação de Bauru?", "quase_respondivel"),
]


def main() -> None:
    eval_set = json.loads((ROOT / "data" / "eval_set.json").read_text("utf-8"))
    itens = []
    for q in eval_set:
        if q["type"] == "semantic":
            itens.append({"pergunta": q["query"], "tipo": "respondivel", "origem": q["id"],
                          "fontes": q["relevant_sources"], "resposta_referencia": None})
    for n in NOVAS:
        itens.append({"pergunta": n["pergunta"], "tipo": "respondivel", "origem": "nova",
                      "fontes": n["fontes"], "resposta_referencia": n["resposta_referencia"]})
    for texto, subtipo in SEM_RESPOSTA:
        itens.append({"pergunta": texto, "tipo": "sem_resposta", "origem": "nova", "subtipo": subtipo,
                      "fontes": [], "resposta_referencia": "Não há resposta no corpus; a resposta correta é informar que a "
                                                           "informação não foi encontrada nos documentos."})
    for i, it in enumerate(itens, 1):
        it["id"] = f"g{i:02d}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
    por_tipo = {t: sum(1 for i in itens if i["tipo"] == t) for t in ("respondivel", "sem_resposta")}
    print(f"{len(itens)} perguntas -> {OUT}  {por_tipo}")


if __name__ == "__main__":
    main()
