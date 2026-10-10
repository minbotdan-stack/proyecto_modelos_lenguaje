
from pathlib import Path
from hashlib import sha256
import json

# 1. Directorio principal del proyecto
BASE = Path(__file__).resolve().parent.parent

ORIGINALES = BASE / "originales"
RESULTADOS = BASE / "resultados"

# 2. Conjuntos y cantidades esperadas
CONJUNTOS = {
    "muestras": 500,
    "transcripciones": 405
}

RESULTADOS.mkdir(exist_ok=True)

# 3. Procesar cada conjunto
for conjunto, esperado in CONJUNTOS.items():

    carpeta = ORIGINALES / conjunto

    archivos = sorted(
        archivo
        for archivo in carpeta.iterdir()
        if archivo.is_file()
        and archivo.suffix.lower() == ".txt"
    )

    # Comprobar cantidad
    if len(archivos) != esperado:
        raise ValueError(
            f"{conjunto}: se esperaban "
            f"{esperado} archivos, "
            f"pero hay {len(archivos)}."
        )

    registros = []
    identificadores = set()

    # 4. Leer los archivos originales
    for archivo in archivos:

        datos = archivo.read_bytes()

        # UTF-8 sin eliminar BOM ni alterar saltos de línea
        texto = datos.decode("utf-8")

        identificador = archivo.stem

        if identificador in identificadores:
            raise ValueError(
                f"ID duplicado: {identificador}"
            )

        identificadores.add(identificador)

        registros.append({
            "id": identificador,
            "archivo": archivo.name,
            "sha256": sha256(datos).hexdigest(),
            "texto_original": texto
        })

    # 5. Construir el documento JSON
    documento = {
        "conjunto": conjunto,
        "formato_original": "txt",
        "cantidad": len(registros),
        "registros": registros
    }

    destino = RESULTADOS / (
        f"{conjunto}_{esperado}.json"
    )

    # 6. Guardar el JSON
    with destino.open(
        "w", encoding="utf-8", newline="\n"
    ) as salida:

        json.dump(
            documento,
            salida,
            ensure_ascii=False,
            indent=2
        )

        salida.write("\n")

    # 7. Validar el archivo generado
    with destino.open(
        "r", encoding="utf-8"
    ) as entrada:

        recuperado = json.load(entrada)

    assert recuperado["cantidad"] == esperado

    for archivo, registro in zip(
        archivos, recuperado["registros"]
    ):

        datos_originales = archivo.read_bytes()
        datos_recuperados = (
            registro["texto_original"].encode("utf-8")
        )

        assert (
            datos_originales == datos_recuperados
        ), f"Contenido diferente: {archivo.name}"

        assert (
            sha256(datos_originales).hexdigest()
            == registro["sha256"]
        ), f"SHA-256 incorrecto: {archivo.name}"

    print(f"\nConjunto: {conjunto}")
    print(f"Registros: {len(registros)}")
    print("Verificacion: CORRECTA")
    print(f"Archivo: {destino.name}")

print("\nConversion finalizada.")
