import requests, time, re
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

headers = {
    "User-Agent": "TCC-RAG-UNESP/1.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
}

body = (
    f"xajax=exibeMenu&xajaxr={int(time.time()*1000)}"
    "&xajaxargs%5B%5D=1&xajaxargs%5B%5D=1&xajaxargs%5B%5D=&xajaxargs%5B%5D="
    "&xajaxargs%5B%5D=&xajaxargs%5B%5D=S&xajaxargs%5B%5D=&xajaxargs%5B%5D="
)
r = requests.post("https://www.fc.unesp.br/", data=body, headers=headers, timeout=15)
cdata_blocks = re.findall(r"<!\[CDATA\[(.*?)\]\]>", r.text, re.DOTALL)
html = " ".join(cdata_blocks)

ids_onclick = re.findall(r"marcaItem\((\d+)", html)
ids_func    = re.findall(r"xajax_exibeCorpo\((\d+)", html)

all_ids = sorted(set(int(x) for x in ids_onclick + ids_func))
print(f"IDs encontrados: {len(all_ids)}")
print("IDs:", all_ids)

# Links com texto associado
soup = BeautifulSoup(html, "lxml")
for a in soup.find_all("a", href=True):
    href = a.get("href", "")
    onclick = a.get("onclick", "")
    m = re.search(r"marcaItem\((\d+)", onclick)
    if m and href:
        print(f"  {m.group(1):>6} -> {href[:80]}  [{a.get_text(strip=True)[:40]}]")
