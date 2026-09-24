import json
from pathlib import Path

datos = json.loads(
    Path("informes_500.json").read_text(encoding="utf-8")
)

informe = next(
    caso for caso in datos["informes"]
    if str(caso["id"]) == "100"
)

salida = Path("informes_exportados/TXT/caso_100.txt")
salida.parent.mkdir(parents=True, exist_ok=True)

# "x" crea el archivo sin sobrescribir uno existente.
with salida.open("x", encoding="utf-8") as archivo:
    archivo.write(informe["texto"] + "\n")

print(f"Recuperado: {salida.resolve()}")