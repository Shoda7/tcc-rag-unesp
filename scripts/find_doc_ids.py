"""
Navega pelas paginas do portal fc.unesp.br usando Playwright,
intercepta as chamadas exibeCorpo para capturar os IDs reais dos itens,
e coleta PDFs encontrados em cada pagina.
"""
import sys, time, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "https://www.fc.unesp.br"

# Rotas que certamente existem (extraidas do menu)
ROUTES = [
    "/#!/graduacao",
    "/#!/ensino/editais/",
    "/#!/oportunidades/editais/",
    "/#!/oportunidades/concursos/",
    "/#!/extensao/",
    "/#!/administracao/diretoria/apresentacao/",
    "/#!/ensino/departamentos/",
    "/#!/ensino/pos-graduacao/",
    "/#!/pesquisa/",
    "/#!/internacional/",
    "/#!/instituicao/historico/",
    "/#!/instituicao/servicos/",
]

found_pdfs = {}   # url -> {pagina, texto}
corpo_calls = {}  # item_id -> route

def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME_PATH)
        context = browser.new_context(user_agent="TCC-RAG-UNESP/1.0 (pesquisa academica)")

        # Bloqueia imagens/fontes para acelerar
        context.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ("image", "media", "font") else route.continue_())

        page = context.new_page()

        def intercept_xhr(request):
            if request.resource_type == "xhr":
                body = request.post_data or ""
                m = re.search(r"xajax=exibeCorpo.*?xajaxargs%5B%5D=(\d+)", body)
                if m:
                    corpo_calls[m.group(1)] = current_route[0]

        page.on("request", intercept_xhr)
        current_route = [""]

        for route in ROUTES:
            url = BASE + route
            current_route[0] = route
            print(f"\n--- Navegando: {route} ---")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                # Aguarda o corpo da pagina ser preenchido
                try:
                    page.wait_for_selector("#idCorpo", timeout=8000)
                except Exception:
                    pass
                time.sleep(3)

                # Coleta todos os PDFs visiveis na pagina
                hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                pdfs = [h for h in hrefs if ".pdf" in h.lower()]
                text = page.inner_text("#idCorpo") if page.query_selector("#idCorpo") else ""

                print(f"  PDFs: {len(pdfs)} | texto corpo: {len(text)} chars")
                for p in pdfs[:5]:
                    print(f"    {p}")
                    found_pdfs[p] = {"route": route, "texto": text[:100]}

            except Exception as e:
                print(f"  ERRO: {e}")

        browser.close()

    print("\n\n=== RESUMO ===")
    print(f"PDFs encontrados: {len(found_pdfs)}")
    for url in found_pdfs:
        print(f"  {url}")

    print(f"\nIDs de exibeCorpo capturados: {len(corpo_calls)}")
    for iid, route in sorted(corpo_calls.items(), key=lambda x: int(x[0])):
        print(f"  id={iid} -> {route}")

if __name__ == "__main__":
    run()
