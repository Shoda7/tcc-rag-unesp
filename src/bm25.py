"""BM25 Okapi (Robertson; Zaragoza, 2009) sobre os chunks indexados.

O PostgreSQL nao implementa BM25: ts_rank e ts_rank_cd ranqueiam por frequencia
e proximidade dos termos (cover density), sem IDF. Este modulo calcula o BM25
em Python, mas reaproveita a normalizacao do proprio PostgreSQL -- a coluna
content_tsv, gerada por to_tsvector('portuguese', unaccent(...)), com stemmer
Snowball, stopwords e remocao de acentos. Assim, FTS e BM25 enxergam exatamente
os mesmos termos e diferem apenas na funcao de ranqueamento.

O indice invertido e montado uma vez por processo, na primeira busca. Depois de
reindexar o banco, reinicie o processo (ou chame reset()).
"""
from __future__ import annotations

import math
from collections import defaultdict

# Parametros classicos do BM25 (Robertson; Zaragoza, 2009)
K1 = 1.2
B = 0.75


class BM25Index:
    def __init__(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT id, source, chunk_index, content FROM chunks ORDER BY id")
            rows = cur.fetchall()
            # unnest(tsvector) devolve cada lexema com suas posicoes; tf = n. de posicoes
            cur.execute(
                "SELECT c.id, u.lexeme, coalesce(array_length(u.positions, 1), 1) "
                "FROM chunks c, unnest(c.content_tsv) u"
            )
            postings_rows = cur.fetchall()

        pos = {row[0]: i for i, row in enumerate(rows)}
        self.docs = [
            {"source": r[1], "chunk_index": r[2], "content": r[3]} for r in rows
        ]
        self.doc_len = [0] * len(rows)
        self.postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for chunk_id, lexeme, tf in postings_rows:
            i = pos[chunk_id]
            self.postings[lexeme].append((i, tf))
            self.doc_len[i] += tf

        self.n_docs = len(rows)
        self.avgdl = sum(self.doc_len) / self.n_docs if self.n_docs else 0.0
        # IDF na variante com +1 (usada no Lucene), que nunca fica negativa
        self.idf = {
            term: math.log(1 + (self.n_docs - len(p) + 0.5) / (len(p) + 0.5))
            for term, p in self.postings.items()
        }

    def score(self, terms: set[str]) -> dict[int, float]:
        scores: dict[int, float] = defaultdict(float)
        for term in terms:
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i, tf in self.postings[term]:
                norm = K1 * (1 - B + B * self.doc_len[i] / self.avgdl)
                scores[i] += idf * tf * (K1 + 1) / (tf + norm)
        return scores


_index: BM25Index | None = None


def get_index(conn) -> BM25Index:
    global _index
    if _index is None:
        _index = BM25Index(conn)
    return _index


def reset() -> None:
    global _index
    _index = None


def query_terms(conn, query: str) -> set[str]:
    """Normaliza a consulta com o mesmo pipeline usado na coluna content_tsv."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT lexeme FROM unnest(to_tsvector('portuguese', unaccent(%s)))",
            (query,),
        )
        return {r[0] for r in cur.fetchall()}


def search(conn, query: str, k: int = 5) -> list[dict]:
    """Retorna os k chunks com maior pontuacao BM25 para a consulta."""
    index = get_index(conn)
    scores = index.score(query_terms(conn, query))
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [{**index.docs[i], "score": s} for i, s in top]
