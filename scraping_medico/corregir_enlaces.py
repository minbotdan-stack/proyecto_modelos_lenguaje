import json
import re
from pathlib import Path
from urllib.parse import quote_plus, unquote_plus

entrada = Path("muestra_500.json")
datos = json.loads(entrada.read_text(encoding="utf-8"))


def codificar(texto):
    return (
        quote_plus(texto, safe="")
        .replace("-", "%2D")
        .replace(".", "%2E")
    )


for caso in datos["casos"]:
    # Separar los dos parámetros conocidos de estos enlaces.
    patron = re.search(
        r"[?&]Type=(.*?)&Sample=(.*)$",
        caso["url"],
        flags=re.IGNORECASE,
    )

    if patron is None:
        raise ValueError(f"Enlace inesperado: {caso['url']}")

    categoria = unquote_plus(patron.group(1))
    muestra = unquote_plus(patron.group(2))

    identificador, separador, titulo = muestra.partition("-")

    if not separador or not identificador.isdigit():
        raise ValueError(f"Identificador inválido: {muestra}")

    caso["url"] = (
        "https://www.mtsamples.com/site/pages/sample.asp"
        f"?Type={codificar(categoria)}"
        f"&Sample={identificador}-{codificar(titulo)}"
    )

salida = Path("muestra_500_corregida.json")
salida.write_text(
    json.dumps(datos, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Archivo creado: {salida.name}")
print("\nPrimer enlace corregido:")
print(datos["casos"][0]["url"])