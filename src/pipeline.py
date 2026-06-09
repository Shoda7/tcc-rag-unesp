"""Orquestrador do pipeline de indexacao via linha de comando.

Etapas:
    scrape   -> baixa PDFs do portal da UNESP (data/raw)
    extract  -> extrai e limpa o texto (data/processed)
    index    -> chunking + embeddings + armazenamento no pgvector
    all      -> extract + index (assume PDFs ja em data/raw)
    search   -> consulta de teste (recuperacao vetorial)
    status   -> mostra contagem de documentos/chunks

Uso:
    python -m src.pipeline scrape
    python -m src.pipeline all
    python -m src.pipeline search "Qual o prazo de entrega do TCC?"
"""
from __future__ import annotations

import argparse

from . import config


def cmd_scrape(args: argparse.Namespace) -> None:
    from .scraper import crawl
    crawl()


def cmd_extract(args: argparse.Namespace) -> None:
    from .extract import extract_all
    extract_all()


def cmd_index(args: argparse.Namespace) -> None:
    from .chunk import chunk_all
    from .embeddings import embed_passages, get_model
    from . import db

    chunks = chunk_all()
    if not chunks:
        return

    model = get_model()
    dim = model.get_sentence_embedding_dimension()

    print(f"\nGerando embeddings de {len(chunks)} chunks...")
    vectors = embed_passages([c.text for c in chunks])

    print("Conectando ao banco e criando esquema...")
    conn = db.connect()
    db.init_schema(conn, dim=dim)
    inserted = db.insert_chunks(conn, chunks, vectors)
    total = db.count_chunks(conn)
    conn.close()
    print(f"\n{inserted} novos chunks inseridos. Total no banco: {total}.")


def cmd_all(args: argparse.Namespace) -> None:
    cmd_extract(args)
    cmd_index(args)


def cmd_search(args: argparse.Namespace) -> None:
    from .embeddings import embed_query
    from . import db

    qvec = embed_query(args.query)
    conn = db.connect()
    results = db.search_vector(conn, qvec, k=args.k)
    conn.close()

    print(f"\nConsulta: {args.query!r}\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['source']} (chunk {r['chunk_index']}) "
              f"sim={r['similarity']:.3f}")
        print(f"    {r['content'][:240]}...\n")


def cmd_fts(args: argparse.Namespace) -> None:
    from . import db

    conn = db.connect()
    results = db.search_fts(conn, args.query, k=args.k)
    conn.close()

    print(f"\nFTS: {args.query!r}\n")
    if not results:
        print("Nenhum resultado.")
        return
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['source']} (chunk {r['chunk_index']}) "
              f"rank={r['rank']:.4f}")
        print(f"    {r['content'][:240]}...\n")


def cmd_status(args: argparse.Namespace) -> None:
    from . import db
    n_raw = len(list(config.DATA_RAW.glob("*.pdf")))
    n_txt = len(list(config.DATA_PROCESSED.glob("*.txt")))
    n_leg = len(list(config.DATA_LEGISLACAO.glob("*.txt")))
    print(f"PDFs em data/raw:            {n_raw}")
    print(f"Textos em data/processed:    {n_txt}")
    print(f"Resoluções em data/legislacao: {n_leg}")
    try:
        conn = db.connect()
        print(f"Chunks no banco:             {db.count_chunks(conn)}")
        conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Banco indisponivel: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de indexacao RAG - UNESP Bauru")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scrape", help="Baixa PDFs do portal da UNESP").set_defaults(func=cmd_scrape)
    sub.add_parser("extract", help="Extrai e limpa o texto dos PDFs").set_defaults(func=cmd_extract)
    sub.add_parser("index", help="Chunking + embeddings + armazenamento").set_defaults(func=cmd_index)
    sub.add_parser("all", help="extract + index").set_defaults(func=cmd_all)
    sub.add_parser("status", help="Mostra o estado da base").set_defaults(func=cmd_status)

    p_search = sub.add_parser("search", help="Consulta de teste (recuperacao vetorial)")
    p_search.add_argument("query", help="Pergunta em linguagem natural")
    p_search.add_argument("-k", type=int, default=5, help="Numero de resultados")
    p_search.set_defaults(func=cmd_search)

    p_fts = sub.add_parser("fts", help="Consulta Full-Text Search (baseline BM25)")
    p_fts.add_argument("query", help="Pergunta em linguagem natural")
    p_fts.add_argument("-k", type=int, default=5, help="Numero de resultados")
    p_fts.set_defaults(func=cmd_fts)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
