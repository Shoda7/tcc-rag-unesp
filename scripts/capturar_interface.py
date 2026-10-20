"""Captura a tela da interface web para o TCC (DOCUMENTO-ENVIO/figuras/fig_interface.png).

Requer o backend (uvicorn app.main:app --port 8000) e o frontend (npm run dev, porta 5173) rodando, o
banco no ar e a chave do Groq no .env. Usa o Microsoft Edge ja instalado (Playwright, canal "msedge"):
nao baixa navegador. Faz a pergunta, espera a resposta, abre a primeira fonte e fotografa.

Uso: python scripts/capturar_interface.py "Pergunta..."
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SAIDA = ROOT / "DOCUMENTO-ENVIO" / "figuras" / "fig_interface.png"
URL = "http://localhost:5173"
PERGUNTA = "Posso usar ChatGPT e ferramentas de IA nos meus trabalhos acadêmicos na UNESP?"


def main() -> int:
    pergunta = sys.argv[1] if len(sys.argv) > 1 else PERGUNTA
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="msedge", headless=True)
        pagina = navegador.new_page(viewport={"width": 980, "height": 1000}, device_scale_factor=2)
        pagina.goto(URL)
        pagina.fill("textarea.input-box", pergunta)
        pagina.click("button.send-btn")
        pagina.wait_for_selector(".bubble.loading")                     # a pergunta foi enviada
        pagina.wait_for_selector(".bubble.loading", state="detached", timeout=240_000)   # a resposta chegou
        pagina.wait_for_selector(".latency")
        resposta = pagina.locator(".msg-bot .bubble-bot").last.inner_text()
        if resposta.startswith("Erro"):
            print("A API devolveu erro:", resposta)
            return 1
        pagina.locator(".source-card").first.click()                    # mostra um trecho de fonte
        pagina.wait_for_timeout(600)
        pagina.evaluate("document.querySelector('.chat').scrollTop = 0")   # pergunta e inicio da resposta
        pagina.wait_for_timeout(400)
        pagina.screenshot(path=str(SAIDA), full_page=False)
        navegador.close()
    print("capturada:", SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
