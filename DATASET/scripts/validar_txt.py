
from pathlib import Path
from collections import Counter, defaultdict
from hashlib import sha256
import csv

# 1. Ubicar el directorio principal
BASE = Path(__file__).resolve().parent.parent

# 2. Definir los conjuntos de datos
CONJUNTOS = {
    "muestras": 500,
    "transcripciones": 405
}

registros = []
hashes = defaultdict(list)

# 3. Recorrer ambos conjuntos
for nombre, cantidad_esperada in CONJUNTOS.items():

    carpeta = BASE / "originales" / nombre

    if not carpeta.is_dir():
        raise SystemExit(f"No existe: {carpeta}")

    archivos = sorted(
        p for p in carpeta.iterdir()
        if p.is_file() and p.suffix.lower() == ".txt"
    )

    print(f"\nConjunto: {nombre}")
    print(f"Esperados: {cantidad_esperada}")
    print(f"Encontrados: {len(archivos)}")

    # 4. Revisar cada archivo
    for archivo in archivos:

        datos = archivo.read_bytes()
        tamaño = len(datos)

        # Huella digital del contenido original
        huella = sha256(datos).hexdigest()
        hashes[huella].append(
            f"{nombre}/{archivo.name}"
        )

        # Comprobar codificación
        try:
            texto = datos.decode("utf-8-sig")
            codificacion = "UTF-8"
        except UnicodeDecodeError:
            try:
                texto = datos.decode("cp1252")
                codificacion = "CP1252 (revisar)"
            except UnicodeDecodeError:
                texto = None
                codificacion = "NO IDENTIFICADA"

        # Detectar posibles problemas
        problemas = []

        if tamaño == 0:
            problemas.append("VACIO")

        if texto is not None and not texto.strip():
            problemas.append("SIN TEXTO UTIL")

        if b"\x00" in datos:
            problemas.append("CONTIENE NULOS")

        if texto is None:
            problemas.append("REVISAR CODIFICACION")

        estado = (
            ", ".join(problemas)
            if problemas else "OK"
        )

        registros.append({
            "conjunto": nombre,
            "archivo": archivo.name,
            "bytes": tamaño,
            "codificacion": codificacion,
            "sha256": huella,
            "estado": estado
        })

# 5. Detectar duplicados exactos
duplicados = {
    h: nombres
    for h, nombres in hashes.items()
    if len(nombres) > 1
}

# 6. Guardar resultados en CSV
salida = BASE / "resultados"
salida.mkdir(exist_ok=True)

archivo_csv = salida / "validacion_archivos.csv"

with archivo_csv.open(
    "w", encoding="utf-8", newline=""
) as f:

    campos = [
        "conjunto", "archivo", "bytes",
        "codificacion", "sha256", "estado"
    ]

    escritor = csv.DictWriter(
        f, fieldnames=campos
    )

    escritor.writeheader()
    escritor.writerows(registros)

# 7. Mostrar resumen
print("\n--- RESUMEN DE VALIDACION ---")
print(f"Total de archivos: {len(registros)}")

conteo_estados = Counter(
    r["estado"] for r in registros
)

conteo_codificaciones = Counter(
    r["codificacion"] for r in registros
)

print("\nEstados:")
for estado, cantidad in conteo_estados.items():
    print(f"{estado}: {cantidad}")

print("\nCodificaciones:")
for cod, cantidad in conteo_codificaciones.items():
    print(f"{cod}: {cantidad}")

print(
    f"\nGrupos de duplicados exactos: "
    f"{len(duplicados)}"
)

for nombres in duplicados.values():
    print("Duplicados:", nombres)

print(f"\nResultado guardado en: {archivo_csv}")
