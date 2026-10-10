
from pathlib import Path
from collections import Counter
import csv
import re

# Directorio principal del proyecto
BASE = Path(__file__).resolve().parent.parent

MUESTRAS = BASE / "originales" / "muestras"
TRANSCRIPCIONES = BASE / "originales" / "transcripciones"
SALIDA = BASE / "resultados" / "inspeccion_estructura.csv"

registros = []

# Analizar los 500 informes
for archivo in sorted(MUESTRAS.glob("*.txt")):

    texto = archivo.read_text(encoding="utf-8-sig")

    campos = {
        "Sample Name": "Sample Name:" in texto,
        "Medical Specialty": "Medical Specialty:" in texto,
        "Description": "Description:" in texto,
        "Report": "(Medical Transcription Sample Report)" in texto
    }

    faltantes = [
        nombre for nombre, presente in campos.items()
        if not presente
    ]

    registros.append({
        "conjunto": "muestras",
        "archivo": archivo.name,
        "id": archivo.stem,
        "fecha": "",
        "hora": "",
        "doctor": "",
        "paciente": "",
        "marcadores": "",
        "observaciones": (
            ", ".join(faltantes)
            if faltantes else "OK"
        )
    })

# Analizar las 405 transcripciones
for archivo in sorted(TRANSCRIPCIONES.glob("*.txt")):

    texto = archivo.read_text(encoding="utf-8-sig")

    fecha = bool(re.search(
        r"^Date of Encounter:", texto, re.MULTILINE
    ))

    hora = bool(re.search(
        r"^Time of Encounter:", texto, re.MULTILINE
    ))

    doctores = re.findall(
        r"^DOCTOR\s+([A-Z]\d+)\s*$",
        texto, re.MULTILINE
    )

    pacientes = re.findall(
        r"^PATIENT\s+([A-Z]\d+)\s*$",
        texto, re.MULTILINE
    )

    observaciones = []

    if not fecha:
        observaciones.append("SIN FECHA")

    if not hora:
        observaciones.append("SIN HORA")

    if not doctores:
        observaciones.append("SIN DOCTOR IDENTIFICADO")

    if not pacientes:
        observaciones.append("SIN PACIENTE IDENTIFICADO")

    identificadores = set(doctores + pacientes)

    if identificadores and identificadores != {archivo.stem}:
        observaciones.append("REVISAR IDENTIFICADOR")

    registros.append({
        "conjunto": "transcripciones",
        "archivo": archivo.name,
        "id": archivo.stem,
        "fecha": fecha,
        "hora": hora,
        "doctor": len(doctores),
        "paciente": len(pacientes),
        "marcadores": texto.count("@@@"),
        "observaciones": (
            ", ".join(observaciones)
            if observaciones else "OK"
        )
    })

# Exportar resultados
SALIDA.parent.mkdir(exist_ok=True)

with SALIDA.open(
    "w", encoding="utf-8", newline=""
) as f:

    escritor = csv.DictWriter(
        f, fieldnames=registros[0].keys()
    )

    escritor.writeheader()
    escritor.writerows(registros)

# Resumen
print("\n--- INSPECCION ESTRUCTURAL ---")

print(f"Total analizado: {len(registros)}")

for conjunto in ["muestras", "transcripciones"]:

    grupo = [
        r for r in registros
        if r["conjunto"] == conjunto
    ]

    correctos = sum(
        r["observaciones"] == "OK"
        for r in grupo
    )

    print(f"\n{conjunto}: {len(grupo)}")
    print(f"Sin observaciones: {correctos}")
    print(f"Para revisar: {len(grupo) - correctos}")

    for registro in grupo:
        if registro["observaciones"] != "OK":
            print(
                registro["archivo"],
                registro["observaciones"]
            )

total_marcadores = sum(
    int(r["marcadores"])
    for r in registros
    if r["conjunto"] == "transcripciones"
)

print(f"\nMarcadores @@@: {total_marcadores}")
print(f"Resultados: {SALIDA}")
