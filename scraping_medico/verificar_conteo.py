import json
from pathlib import Path
from collections import Counter

datos = json.loads(
    Path("informes_500.json").read_text(encoding="utf-8")
)

informes = datos["informes"]
seleccionados = datos["muestra"]["casos"]

conteo = Counter(str(informe["id"]) for informe in informes)
guardados = set(conteo)

# Buscar TXT tanto en informes_exportados como en su subcarpeta TXT.
carpeta = Path("informes_exportados")
archivos = list(carpeta.rglob("caso_*.txt"))
ids_txt = {archivo.stem.removeprefix("caso_") for archivo in archivos}

print("Informes dentro del JSON:", len(informes))
print("Identificadores únicos en el JSON:", len(guardados))
print("Archivos TXT encontrados:", len(archivos))
print("Identificadores únicos en TXT:", len(ids_txt))

print("\nIDs repetidos en el JSON:")
print({id_: veces for id_, veces in conteo.items() if veces > 1})

print("\nCasos seleccionados que NO están en el JSON:")
pendientes = [
    caso for caso in seleccionados
    if str(caso["id"]) not in guardados
]
for caso in pendientes:
    print(caso["id"], caso["titulo"])
    print(caso["url"])
if not pendientes:
    print("Ninguno.")

print("\nInformes del JSON que NO tienen TXT:")
faltantes = guardados - ids_txt
for id_ in sorted(faltantes, key=int):
    print(f"caso_{id_}.txt")
if not faltantes:
    print("Ninguno.")