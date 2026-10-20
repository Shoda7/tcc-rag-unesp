"""Gera as figuras do TCC em DOCUMENTO-ENVIO/figuras/ (PNG, 300 dpi).

    fig_arquitetura.png   arquitetura do sistema (indexacao e consulta)
    fig_corpus.png        composicao do corpus: resolucoes por ano e distribuicao do tamanho

Os numeros do corpus sao calculados a partir de data/legislacao/; os do pipeline (chunks, dimensoes)
vem de data/resultados_resumo.json e de src/config.py, para nao divergirem do texto.

Uso: python scripts/gerar_figuras.py
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import config  # noqa: E402

OUT = ROOT / "DOCUMENTO-ENVIO" / "figuras"
LEG = ROOT / "data" / "legislacao"

AZUL = "#2a78d6"            # azul unico (paleta de referencia): serie unica, sem legenda
AZUL_CLARO = "#cfe0f6"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRADE = "#dcdbd5"

plt.rcParams.update({
    "font.family": "Times New Roman", "font.size": 9, "axes.edgecolor": TINTA_2, "axes.labelcolor": TINTA,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2, "text.color": TINTA, "savefig.dpi": 300,
    "axes.spines.top": False, "axes.spines.right": False,
})


def n_br(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


# ── Figura 1: arquitetura ─────────────────────────────────────────────────────

def caixa(ax, x, y, w, h, linhas, tracejado=False, destaque=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=2.2",
                                linewidth=1.1, edgecolor=AZUL, facecolor=AZUL_CLARO if destaque else "white",
                                linestyle="--" if tracejado else "-"))
    titulo, *resto = linhas
    ax.text(x + w / 2, y + h - 4.2, titulo, ha="center", va="top", fontsize=9, fontweight="bold")
    ax.text(x + w / 2, y + h - 10.5, "\n".join(resto), ha="center", va="top", fontsize=8, color=TINTA_2, linespacing=1.35)


def seta(ax, p0, p1, rad=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=9, linewidth=1.1, color=TINTA_2,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))


def fig_arquitetura() -> Path:
    n_chunks = 4229
    fig, ax = plt.subplots(figsize=(6.3, 4.1))
    ax.set_xlim(-1.5, 101.5)
    ax.set_ylim(0, 100)
    ax.axis("off")
    w, h, gap = 22, 29, (100 - 4 * 22) / 3

    ax.text(0, 97, "(a) Indexação (executada uma vez)", fontsize=9.5, fontstyle="italic", va="top")
    topo = 62
    colunas = [i * (w + gap) for i in range(4)]
    a = [
        ["Coleta", "portal de legislação", "da UNESP → scraper", "936 resoluções (.txt)"],
        ["Segmentação", "janela deslizante:", f"{config.CHUNK_SIZE_WORDS} palavras, {config.CHUNK_OVERLAP_WORDS} de", "sobreposição", f"{n_br(n_chunks)} trechos"],
        ["Embeddings", config.EMBEDDING_MODEL.split("/")[-1], f"{config.EMBEDDING_DIM} dimensões", "(execução local)"],
        ["PostgreSQL 16", "+ pgvector", "HNSW (cosseno)", "GIN (tsvector)"],
    ]
    for x, linhas in zip(colunas, a):
        caixa(ax, x, topo, w, h, linhas, destaque=linhas[0].startswith("PostgreSQL"))
    for i in range(3):
        seta(ax, (colunas[i] + w + 0.8, topo + h / 2), (colunas[i + 1] - 0.8, topo + h / 2))

    ax.text(0, 49, "(b) Consulta (a cada pergunta)", fontsize=9.5, fontstyle="italic", va="top")
    base = 8
    b = [
        ["Interface web", "React + Vite", "recebe a pergunta"],
        ["API FastAPI", "recupera 5 trechos:", "vetorial, BM25,", "FTS-PG ou híbrido"],
        ["Geração", "gpt-oss-120b (Groq)", "prompt com os trechos", "e pedido de citação"],
        ["Resposta", "texto com resoluções", "citadas e trechos", "usados como fonte"],
    ]
    for i, (x, linhas) in enumerate(zip(colunas, b)):
        caixa(ax, x, base, w, h, linhas, tracejado=(i == 2))
    for i in range(3):
        seta(ax, (colunas[i] + w + 0.8, base + h / 2), (colunas[i + 1] - 0.8, base + h / 2))

    # banco -> API (cotovelo): desce do PostgreSQL, anda ate a API e desce ate ela
    x_db, x_api = colunas[3] + w / 2, colunas[1] + w / 2
    y_meio = 55
    ax.plot([x_db, x_db], [topo - 0.4, y_meio], color=TINTA_2, linewidth=1.1)
    ax.plot([x_db, x_api], [y_meio, y_meio], color=TINTA_2, linewidth=1.1)
    seta(ax, (x_api, y_meio), (x_api, base + h + 0.9))
    ax.text((x_db + x_api) / 2, y_meio + 1.6, "consulta ao índice", ha="center", va="bottom", fontsize=7.5, color=TINTA_2)

    ax.text(100, 1.5, "Contorno tracejado: serviço externo (API do Groq).", ha="right", va="bottom", fontsize=7.5, color=TINTA_2)
    caminho = OUT / "fig_arquitetura.png"
    fig.savefig(caminho, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return caminho


# ── Figura 2: corpus ──────────────────────────────────────────────────────────

def fig_corpus() -> Path:
    arqs = sorted(LEG.glob("resolucao_*.txt"))
    por_ano = Counter(int(a.name.split("_")[1]) for a in arqs)
    palavras = np.array([len(a.read_text(encoding="utf-8").split()) for a in arqs])
    mediana = statistics.median(palavras)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.3, 2.7), gridspec_kw={"width_ratios": [1.15, 1]})
    anos = sorted(por_ano)
    valores = [por_ano[a] for a in anos]
    cores = [AZUL] * len(anos)
    cores[-1] = AZUL_CLARO                       # 2026: ano incompleto (coleta em junho)
    barras = ax1.bar([str(a) for a in anos], valores, color=cores, width=0.68, edgecolor=AZUL, linewidth=0.8)
    for b, v in zip(barras, valores):
        ax1.text(b.get_x() + b.get_width() / 2, v + 2, str(v), ha="center", va="bottom", fontsize=7.5, color=TINTA_2)
    ax1.set_ylabel("Resoluções")
    ax1.set_title("(a) Resoluções por ano", fontsize=9.5, loc="left", fontstyle="italic")
    ax1.tick_params(axis="x", labelrotation=60, labelsize=8)
    ax1.set_ylim(0, max(valores) * 1.14)
    ax1.yaxis.grid(True, color=GRADE, linewidth=0.7)
    ax1.set_axisbelow(True)
    ax1.text(0.01, 0.97, "2026: ano incompleto\n(coleta em jun/2026)", transform=ax1.transAxes, ha="left", va="top",
             fontsize=7.5, color=TINTA_2)

    bins = np.logspace(np.log10(palavras.min()), np.log10(palavras.max()), 26)
    ax2.hist(palavras, bins=bins, color=AZUL, edgecolor="white", linewidth=0.6)
    ax2.set_xscale("log")
    topo = ax2.get_ylim()[1] * 1.3
    ax2.set_ylim(0, topo)
    ax2.axvline(mediana, color=TINTA, linewidth=1.0, linestyle="--", label=f"mediana ({n_br(mediana)} palavras)")
    ax2.axvline(config.CHUNK_SIZE_WORDS, color=TINTA_2, linewidth=1.0, linestyle=":",
                label=f"tamanho do trecho ({config.CHUNK_SIZE_WORDS})")
    ax2.legend(loc="upper right", frameon=False, fontsize=7.5, handlelength=2.4)
    ax2.set_xlabel("Palavras por resolução (escala logarítmica)")
    ax2.set_ylabel("Resoluções")
    ax2.set_title("(b) Tamanho das resoluções", fontsize=9.5, loc="left", fontstyle="italic")
    ax2.yaxis.grid(True, color=GRADE, linewidth=0.7)
    ax2.set_axisbelow(True)
    ax2.set_xticks([100, 300, 1000, 3000, 10000])
    ax2.set_xticklabels(["100", "300", "1.000", "3.000", "10.000"])

    fig.tight_layout()
    caminho = OUT / "fig_corpus.png"
    fig.savefig(caminho, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return caminho


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (fig_arquitetura(), fig_corpus()):
        print("gerada:", f)


if __name__ == "__main__":
    main()
