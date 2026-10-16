import json
import os
import re
from collections import defaultdict, Counter

CARPETA = "500_informes_tokenizados"
SALIDA = "conteo.json"
IGNORAR = {"SAMPLE NAME", "MEDICAL SPECIALTY"}
LIMITE_ARCHIVOS = None


def normalizar(k):
    return re.sub(r"\s+", " ", k.strip().upper())


info = defaultdict(lambda: {"conteo": 0, "ejemplos": [], "hermanas": Counter()})

archivos = sorted(n for n in os.listdir(CARPETA) if n.endswith(".json"))
if LIMITE_ARCHIVOS:
    archivos = archivos[:LIMITE_ARCHIVOS]

procesados = 0
for nombre in archivos:
    ruta = os.path.join(CARPETA, nombre)
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print("Archivo con problema:", nombre, "-", e)
        continue

    if not isinstance(datos, dict):
        print("Se esperaba un diccionario en:", nombre)
        continue

    # Claves normalizadas de este informe (sin metadatos)
    claves = {normalizar(k) for k in datos} - IGNORAR

    for k_original, valor in datos.items():
        k = normalizar(k_original)
        if k in IGNORAR:
            continue
        d = info[k]
        d["conteo"] += 1
        if isinstance(valor, str) and len(d["ejemplos"]) < 3:
            d["ejemplos"].append(valor[:150])
        if len(k) <= 4:                          # hermanas solo para claves cortas
            d["hermanas"].update(h for h in claves if h != k)

    procesados += 1

salida = {
    k: {
        "conteo": d["conteo"],
        "ejemplos": d["ejemplos"],
        "hermanas": dict(d["hermanas"].most_common(8)),   # las 8 más frecuentes
    }
    for k, d in sorted(info.items(), key=lambda x: -x[1]["conteo"])
}

with open(SALIDA, "w", encoding="utf-8") as f:
    json.dump(salida, f, indent=2, ensure_ascii=False)

print("Informes procesados:", procesados)
print("Claves distintas:", len(salida))
print("Aparecen en >=5 informes:", sum(1 for d in salida.values() if d["conteo"] >= 5))