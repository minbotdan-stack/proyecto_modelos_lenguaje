from pathlib import Path
import re

from bs4 import BeautifulSoup, Comment

# 1. Leer el HTML guardado desde el navegador.
entrada = Path("informe.html")
soup = BeautifulSoup(entrada.read_bytes(), "html.parser")

# 2. Encontrar el recuadro que aparece después del informe.
etiqueta_final = soup.find(
    "strong",
    string=lambda texto: (
        texto is not None
        and texto.strip() == "About This Sample:"
    ),
)

if etiqueta_final is None:
    raise SystemExit(
        "No se encontró 'About This Sample'. "
        "Revisa que guardaste la página completa del informe."
    )

fin = etiqueta_final.find_parent("div")

# El informe comienza después del <hr> anterior a ese recuadro.
inicio = fin.find_previous_sibling("hr")

if inicio is None:
    raise SystemExit("No se encontró el inicio del informe.")

# 3. Recoger únicamente el HTML entre esos dos límites.
fragmentos = []

for elemento in inicio.next_siblings:
    if elemento is fin:
        break

    if not isinstance(elemento, Comment):
        fragmentos.append(str(elemento))

bloque = BeautifulSoup("".join(fragmentos), "html.parser")

# 4. Eliminar publicidad y código que no pertenece al informe.
for elemento in bloque.select(
    "script, style, ins, iframe, .adsbygoogle"
):
    elemento.decompose()

# 5. Convertir los saltos HTML a saltos de línea de texto.
for salto in bloque.find_all("br"):
    salto.replace_with("\n")

texto = bloque.get_text().replace("\xa0", " ")

# Limpiar espacios sobrantes sin cambiar palabras ni secciones.
lineas = [
    re.sub(r"[ \t]+", " ", linea).strip()
    for linea in texto.splitlines()
]

texto = "\n".join(lineas)
texto = re.sub(r"\n{3,}", "\n\n", texto).strip()

if not texto:
    raise SystemExit("El texto extraído está vacío.")

# 6. Guardar el informe en TXT.
salida = Path("informe.txt")
salida.write_text(texto + "\n", encoding="utf-8")

print(f"Archivo creado: {salida.resolve()}")
print(f"Caracteres extraídos: {len(texto)}")
print("\nVista previa:\n")
print(texto[:500])