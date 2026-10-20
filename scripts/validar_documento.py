"""Valida o documento do TCC contra os dados e o codigo do repositorio.

Confere, em DOCUMENTO-ENVIO/TCC_RAG_UNESP_Bauru.docx:
  1. sobras de template/erro ("undefined", "NaN", "${", "[object")
  2. numeros-chave do texto x data/resultados_resumo.json, corpus_release.json e config_sistema.json
  3. modelo de embedding, modelo de LLM, k1/b e parametros do RRF x codigo
  4. caminhos de arquivos citados no texto existem no repositorio
  5. toda referencia e citada no texto
  6. toda "Tabela/Figura/Quadro N" citada tem legenda e vice-versa
  7. numeracao de secoes sequencial
  8. pendencias conhecidas ([a definir], ano da capa)

Saida: lista de problemas (exit 1) ou "OK". Os avisos nao reprovam.

Uso: python scripts/validar_documento.py
"""
from __future__ import annotations

import html
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "DOCUMENTO-ENVIO" / "TCC_RAG_UNESP_Bauru.docx"


def paragrafos() -> list[str]:
    xml = zipfile.ZipFile(DOCX).read("word/document.xml").decode("utf-8")
    return [t for t in (html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)) if t]


def br(x: float, d: int = 3) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def main() -> int:
    erros: list[str] = []
    avisos: list[str] = []
    paras = paragrafos()
    texto = "\n".join(paras)
    i_ref = max(i for i, p in enumerate(paras) if p.upper() == "REFERÊNCIAS")
    # o corpo começa no ÚLTIMO "1 INTRODUÇÃO": depois que o Word preenche o sumário, ele também tem essa
    # linha (e todas as seções), que não devem ser lidas como texto do trabalho
    i_corpo = max(i for i, p in enumerate(paras[:i_ref]) if p.startswith("1 INTRODU"))
    corpo = "\n".join(paras[i_corpo:i_ref])
    # as referências terminam onde começam os apêndices
    i_ap = next((i for i, p in enumerate(paras) if i > i_ref and p.upper().startswith("APÊNDICE")), len(paras))
    refs = paras[i_ref + 1:i_ap]

    # 1. sobras
    for ruim in ("undefined", "NaN", "${", "[object"):
        if ruim in texto:
            erros.append(f"sobra de template/erro no texto: '{ruim}'")

    # 2. numeros x dados
    R = json.loads((ROOT / "data" / "resultados_resumo.json").read_text("utf-8"))
    G, T = R["global"], R["por_tipo"]
    esperados = {
        "MRR do hibrido": br(G["rrf"]["mrr"]), "MRR do BM25": br(G["bm25"]["mrr"]),
        "MRR da vetorial": br(G["vec"]["mrr"]), "MRR do FTS-PG": br(G["fts"]["mrr"]),
        "Hit@1 do hibrido": br(G["rrf"]["hit1"]), "MRR semantico do hibrido": br(T["semantic"]["rrf"]["mrr"]),
    }
    for nome, v in esperados.items():
        if v not in texto:
            erros.append(f"{nome} ({v}) nao aparece no texto: documento desatualizado em relacao a resultados_resumo.json?")
    for n, rotulo in ((R["meta"]["n_consultas"], "consultas"),):
        if f"{n} {rotulo}" not in texto:
            avisos.append(f"'{n} {rotulo}' nao aparece literalmente")
    C = json.loads((ROOT / "data" / "corpus_release.json").read_text("utf-8"))
    if C["sha256_pacote"] not in texto:
        erros.append("o SHA-256 do corpus no texto difere de data/corpus_release.json")
    n_leg = len(list((ROOT / "data" / "legislacao").glob("resolucao_*.txt")))
    if n_leg != C["documentos"] or f"{n_leg} resoluções" not in texto:
        erros.append(f"numero de resolucoes: {n_leg} em disco, {C['documentos']} em corpus_release.json, texto cita '{n_leg} resoluções'?")

    # 3. parametros x codigo
    sys.path.insert(0, str(ROOT))
    from src import bm25, config, db  # noqa: E402
    for rotulo, v in (("modelo de embedding", config.EMBEDDING_MODEL.split("/")[-1]), ("modelo de LLM", config.GROQ_MODEL.split("/")[-1]),
                      ("dimensao", str(config.EMBEDDING_DIM))):
        if v not in texto:
            erros.append(f"{rotulo} do codigo ('{v}') nao aparece no texto")
    if f"k₁ = {br(bm25.K1, 1)}" not in texto or f"b = {br(bm25.B, 2)}" not in texto:
        erros.append("parametros do BM25 (k1, b) do codigo nao batem com o texto")
    if f"ef_search = {db.HNSW_EF_SEARCH}" not in texto:
        erros.append(f"hnsw.ef_search do codigo ({db.HNSW_EF_SEARCH}) nao aparece no texto")
    for velho in ("llama-3.3-70b-versatile", "multilingual-e5-large", "plainto_tsquery, e combina"):
        if velho in texto and velho != "plainto_tsquery, e combina":
            avisos.append(f"termo antigo no texto: '{velho}' (confira se e menção histórica)")

    # 4. caminhos citados existem
    for caminho in sorted(set(re.findall(r"\b(?:src|scripts|app|frontend|data)/[\w./-]+", corpo))):
        c = caminho.rstrip(".,;:)")
        if not (ROOT / c).exists() and not any(ROOT.glob(c + "*")) and "AAAA" not in c:
            erros.append(f"caminho citado no texto nao existe: {c}")

    # 5. referencias citadas
    for r in refs:
        sobrenome = re.split(r"[,;.]", r)[0].strip()
        busca = "pgvector" if sobrenome.upper() == "PGVECTOR" else sobrenome
        if not re.search(re.escape(busca), corpo, flags=re.I):
            erros.append(f"referencia nao citada no texto: {sobrenome}")
    if len(refs) < 20:
        avisos.append(f"apenas {len(refs)} referencias (meta: >= 20)")

    # 6. tabelas, figuras e quadros
    for tipo in ("Tabela", "Figura", "Quadro"):
        legendas = set(re.findall(rf"^{tipo} (\d+) —", corpo, flags=re.M))
        sem_legendas = "\n".join(l for l in corpo.splitlines() if not re.match(rf"^{tipo} \d+ —", l))
        citadas = set(re.findall(rf"{tipo} (\d+)\b", sem_legendas))   # citações no texto, sem contar a própria legenda
        for n in sorted(citadas - legendas, key=int):
            erros.append(f"'{tipo} {n}' e citada mas nao tem legenda")
        for n in sorted(legendas - citadas, key=int):
            erros.append(f"'{tipo} {n}' tem legenda mas nunca e citada no texto")
        if legendas and sorted(map(int, legendas)) != list(range(1, len(legendas) + 1)):
            erros.append(f"numeracao de {tipo}s nao sequencial: {sorted(map(int, legendas))}")

    # 7. secoes
    secoes = re.findall(r"^(\d+(?:\.\d+)+) \S", corpo, flags=re.M)
    vistos: dict[str, int] = {}
    for s in secoes:
        pai, _, filho = s.rpartition(".")
        n = int(filho)
        if n != vistos.get(pai, 0) + 1:
            erros.append(f"numeracao de secoes: {s} depois de {pai}.{vistos.get(pai, 0)}")
        vistos[pai] = n

    # 7b. toda sigla da lista de siglas e usada no corpo do texto (a ABNT lista so as usadas)
    try:
        a = next(i for i, p in enumerate(paras) if p.upper() == "LISTA DE ABREVIATURAS E SIGLAS")
        b = next(i for i, p in enumerate(paras) if i > a and p.upper() == "SUMÁRIO")
        siglas = paras[a + 1:b][::2]                       # a tabela gera: sigla, significado, sigla, significado...
        corpo_tx = corpo
        for s in siglas:
            if not re.search(rf"(?<![\w-]){re.escape(s)}(?![\w-])", corpo_tx):
                erros.append(f"sigla na lista mas nao usada no texto: {s}")
    except StopIteration:
        avisos.append("lista de abreviaturas e siglas nao encontrada")

    # 8. pendencias conhecidas
    if "a definir" in texto:
        avisos.append("folha de aprovacao: nomes da banca ainda a definir")
    if re.search(r"Bauru\s+2026", texto):
        avisos.append("capa/folha de rosto com ano 2026 (a entrega e em 2027)")

    for a in avisos:
        print("AVISO:", a)
    for e in erros:
        print("ERRO: ", e)
    print(f"\n{len(erros)} erro(s), {len(avisos)} aviso(s); {len(paras)} paragrafos, {len(refs)} referencias, {len(texto.split())} palavras.")
    if not erros:
        print("OK")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
