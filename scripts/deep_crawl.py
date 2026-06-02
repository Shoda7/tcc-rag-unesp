"""
Crawl profundo: navega pelas paginas de Graduacao e SI do portal fc.unesp.br,
coletando todos os PDFs encontrados e mapeando os sub-links de cada pagina.
"""
import sys, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "https://www.fc.unesp.br"
VISITED = set()
ALL_PDFS = {}

def collect_page(page, url, depth=0):
    if url in VISITED or depth > 3:
        return
    VISITED.add(url)
    indent = "  " * depth

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        time.sleep(3)

        hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        text = page.inner_text("body")

        pdfs = [h for h in hrefs if ".pdf" in h.lower() and "fc.unesp.br" in h]
        sub_links = [
            h for h in set(hrefs)
            if "fc.unesp.br/#!/" in h
            and h not in VISITED
        ]

        print(f"{indent}[d={depth}] {url}")
        print(f"{indent}  pdfs={len(pdfs)} sublinks={len(sub_links)}")

        # Verifica se e uma pagina com conteudo sobre SI ou TCC
        keywords = ["sistemas de informa", "tcc", "trabalho de conclus", "regulamento",
                    "regimento", "edital", "bolsa", "cepe", "resolucao", "resolução"]
        has_keyword = any(kw in text.lower() for kw in keywords)
        if has_keyword:
            print(f"{indent}  *** PAGINA RELEVANTE *** (keywords: {[k for k in keywords if k in text.lower()][:3]})")

        for p in set(pdfs):
            if p not in ALL_PDFS:
                ALL_PDFS[p] = url
                print(f"{indent}  PDF: {p}")

        # Prioriza links sobre graduacao, SI, TCC, regulamento
        priority_links = [l for l in sub_links if any(
            kw in l.lower() for kw in ["graduacao", "sistemas", "tcc", "regulamento",
                                        "edital", "bolsa", "regimento", "resolucao"]
        )]
        other_links = [l for l in sub_links if l not in priority_links]

        for link in priority_links[:10] + other_links[:5]:
            collect_page(page, link, depth + 1)

    except Exception as e:
        print(f"{indent}  ERRO: {e}")


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME_PATH)
        context = browser.new_context(user_agent="TCC-RAG-UNESP/1.0 (pesquisa academica)")
        context.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ("image", "media", "font") else route.continue_())
        page = context.new_page()

        # Começa pelas paginas mais relevantes
        start_urls = [
            f"{BASE}/#!/graduacao",
            f"{BASE}/#!/ensino/editais/",
            f"{BASE}/#!/oportunidades/editais/",
        ]
        for url in start_urls:
            collect_page(page, url, depth=0)

        browser.close()

    print("\n\n=== TODOS OS PDFs ENCONTRADOS ===")
    print(f"Total: {len(ALL_PDFS)}")
    for pdf_url, origin in ALL_PDFS.items():
        print(f"  {pdf_url}")
        print(f"    (origem: {origin})")


if __name__ == "__main__":
    run()
