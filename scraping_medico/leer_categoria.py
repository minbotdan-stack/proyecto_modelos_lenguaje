from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

ruta = Path("categoria.html")
html = ruta.read_text(encoding="utf-8", errors="replace")
soup = BeautifulSoup(html, "html.parser")

base = "https://www.mtsamples.com/site/pages/"
casos = {}

for etiqueta in soup.find_all("a", href=True):
    url = urljoin(base, etiqueta["href"])
    partes = urlparse(url)

    if not partes.path.lower().endswith("/sample.asp"):
        continue

    parametros = {
        clave.lower(): valores
        for clave, valores in parse_qs(partes.query).items()
    }

    sample = parametros.get("sample", [""])[0]
    identificador = sample.split("-", 1)[0]

    if not identificador.isdigit():
        continue

    casos.setdefault(
        identificador,
        {
            "titulo": etiqueta.get_text(" ", strip=True),
            "url": url,
        },
    )

print(f"Enlaces únicos a informes encontrados: {len(casos)}")

for caso in list(casos.values())[:5]:
    print(caso["titulo"])
    print(caso["url"])
    print()


import random
import json

# Conservar únicamente enlaces de la categoría 97.
casos_categoria = []

for identificador, caso in casos.items():
    parametros = {
        clave.lower(): valores
        for clave, valores in parse_qs(
            urlparse(caso["url"]).query
        ).items()
    }

    categoria = parametros.get("type", [""])[0]

    if categoria.split("-", 1)[0] == "97":
        casos_categoria.append({
            "id": identificador,
            "titulo": caso["titulo"],
            "url": caso["url"],
        })

# Orden estable para poder repetir el muestreo.
casos_categoria.sort(key=lambda caso: int(caso["id"]))

print(f"Casos confirmados de la categoría 97: {len(casos_categoria)}")

if len(casos_categoria) < 500:
    raise SystemExit("No hay 500 enlaces válidos de esta categoría.")

semilla = 42
muestra = random.Random(semilla).sample(casos_categoria, 500)

resultado = {
    "categoria": "Consult - History and Phy.",
    "semilla": semilla,
    "total_candidatos": len(casos_categoria),
    "cantidad_seleccionada": len(muestra),
    "casos": muestra,
}

Path("muestra_500.json").write_text(
    json.dumps(resultado, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("Muestra guardada en muestra_500.json")