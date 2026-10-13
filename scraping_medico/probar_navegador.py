import json
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

muestra = json.loads(Path("muestra_500_corregida.json").read_text(encoding="utf-8"))

caso = muestra["casos"][0]

with sync_playwright() as p:
    navegador = p.chromium.launch(headless=False)
    pagina = navegador.new_page()

    try:
        print("Abriendo:", caso["titulo"])

        pagina.goto(caso["url"],
            wait_until="domcontentloaded",
            timeout=60000,
        )

        respuesta = input(
            "\nGuardar HTML?"
        ).strip().lower()

        if respuesta not in ("si"):
            raise SystemExit("No se guardó el HTML.")

        html = pagina.content()
        soup = BeautifulSoup(html, "html.parser")

        marcador = soup.find(
            "strong",
            string=lambda texto: (
                texto is not None
                and texto.strip() == "About This Sample:"
            ),
        )

        if marcador is None:
            raise SystemExit(
                "No aparece el marcador esperado del informe. "
                "No se guardará esta página."
            )

        salida = Path(f"prueba_{caso['id']}.html")
        salida.write_text(html, encoding="utf-8")

        print(f"\nHTML guardado: {salida.resolve()}")

    finally:
        navegador.close()