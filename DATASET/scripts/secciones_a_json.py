from pathlib import Path
import json
import re


# ---------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

CARPETA_ENTRADA = BASE_DIR / "originales" / "muestras"
CARPETA_SALIDA = BASE_DIR / "resultados" / "secciones_prueba"

CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# ENCABEZADOS MEDICOS CONOCIDOS
# ---------------------------------------------------------

ENCABEZADOS_PRINCIPALES = {
    "CHIEF COMPLAINT",
    "CHIEF REASON FOR CONSULTATION",
    "HISTORY OF PRESENT ILLNESS",
    "HISTORY OF PRESENT PROBLEM",
    "BRIEF HISTORY OF PRESENT ILLNESS",
    "HISTORY",
    "PAST MEDICAL HISTORY",
    "PAST MEDICAL HX",
    "PAST SURGICAL HISTORY",
    "PAST SURGICAL HX",
    "PAST HISTORY",
    "MEDICATIONS",
    "ALLERGIES",
    "FAMILY HISTORY",
    "SOCIAL HISTORY",
    "SOCIAL HX",
    "REVIEW OF SYSTEMS",
    "PHYSICAL EXAM",
    "PHYSICAL EXAMINATION",
    "PE",
    "CLINICAL/PHYSICAL EXAMINATION",
    "RADIOGRAPHS",
    "LABORATORY STUDIES",
    "RADIOLOGICAL/LABORATORY EXAM",
    "IMPRESSION",
    "CLINICAL IMPRESSION",
    "ASSESSMENT",
    "PLAN",
    "TREATMENT PLAN",
    "EVALUATION/TREATMENT PLAN",
    "DISPOSITION",
    "SUBJECTIVE",
    "OBJECTIVE",
    "A",
    "P",
}




ENCABEZADOS_EXAMEN = {
    "PHYSICAL EXAM",
    "PHYSICAL EXAMINATION",
    "PE",
    "CLINICAL/PHYSICAL EXAMINATION",
}




def normalizar_saltos(texto):
    return texto.replace("\r\n", "\n").replace("\r", "\n")




def detectar_encabezado(linea, linea_anterior_vacia, dentro_examen):
    """
    Determina si una linea representa un encabezado principal.

    Devuelve:
        (llave, contenido)
    
    o:
        None
    """

    texto = linea.strip()

    if not texto or ":" not in texto:
        return None

    llave, contenido = texto.split(":", 1)
    llave = llave.strip()
    contenido = contenido.strip()

    # Encabezado conocido
    if llave in ENCABEZADOS_PRINCIPALES:
        return llave, contenido

    # Si estamos dentro del examen físico,
    # evitamos interpretar GENERAL, NECK, CHEST,
    # ABDOMEN, etc. como nuevas secciones principales.
    if dentro_examen:
        return None

    # Posible encabezado desconocido:
    # debe estar en mayúsculas y comenzar después
    # de una línea vacía.
    if linea_anterior_vacia:
        patron = r"[A-Z][A-Z0-9 /&().,\-+'\"’–—#]*"

        if re.fullmatch(patron, llave) and len(llave) >= 3:
            return llave, contenido

    return None




def extraer_metadatos(lineas):
    datos = {}

    for i, linea in enumerate(lineas):

        texto = linea.strip()

        coincidencia = re.match(
            r"^(Sample Name|Medical Specialty|Description):\s*(.*)$",
            texto,
            re.IGNORECASE
        )

        if not coincidencia:
            continue

        llave = coincidencia.group(1)
        valor = coincidencia.group(2).strip()

        # Medical Specialty muchas veces tiene el valor
        # en la siguiente linea.
        if llave.lower() == "medical specialty" and not valor:

            j = i + 1

            while j < len(lineas) and not lineas[j].strip():
                j += 1

            if j < len(lineas):
                siguiente = lineas[j].strip()

                if not siguiente.startswith("("):
                    valor = siguiente

        datos[llave] = valor

    return datos




def convertir_txt(ruta_txt):

    texto = ruta_txt.read_text(encoding="utf-8")
    texto = normalizar_saltos(texto)

    lineas = texto.splitlines()

    datos = extraer_metadatos(lineas)



    inicio = 0

    for i, linea in enumerate(lineas):

        if linea.strip().lower() == "(medical transcription sample report)":
            inicio = i + 1
            break



    secciones = {}

    seccion_actual = None
    contenido_actual = []

    linea_anterior_vacia = True
    dentro_examen = False

    texto_sin_encabezado = []

    def guardar_seccion():

        nonlocal seccion_actual
        nonlocal contenido_actual
        nonlocal dentro_examen

        if seccion_actual is None:
            return

        contenido = "\n".join(contenido_actual).strip()

        secciones[seccion_actual] = contenido

        seccion_actual = None
        contenido_actual = []
        dentro_examen = False

    for linea in lineas[inicio:]:

        encabezado = detectar_encabezado(
            linea,
            linea_anterior_vacia,
            dentro_examen
        )

        if encabezado:

            guardar_seccion()

            seccion_actual, contenido = encabezado

            if contenido:
                contenido_actual.append(contenido)

            dentro_examen = seccion_actual in ENCABEZADOS_EXAMEN

        else:

            if seccion_actual is None:

                if linea.strip():
                    texto_sin_encabezado.append(linea)

            else:

                contenido_actual.append(linea)

        linea_anterior_vacia = not bool(linea.strip())

    # Guardar última sección
    guardar_seccion()



    texto_inicial = "\n".join(texto_sin_encabezado).strip()

    if texto_inicial:
        secciones["REPORT"] = texto_inicial



    resultado = {}

    resultado.update(datos)
    resultado.update(secciones)

    return resultado


# ---------------------------------------------------------
# PROCESAR ARCHIVOS DE PRUEBA
# ---------------------------------------------------------

def main():

    archivos = sorted(CARPETA_ENTRADA.glob("*.txt"))

    if not archivos:
        print("No se encontraron archivos TXT.")
        return

    print("Archivos encontrados:", len(archivos))
    print()

    # Por ahora solamente procesamos los primeros 3.
    archivos_prueba = archivos[:3]

    for ruta_txt in archivos_prueba:

        print("Procesando:", ruta_txt.name)

        resultado = convertir_txt(ruta_txt)

        ruta_json = CARPETA_SALIDA / f"{ruta_txt.stem}.json"

        ruta_json.write_text(
            json.dumps(
                resultado,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        print("JSON creado:", ruta_json)
        print("Llaves detectadas:")

        for llave in resultado:
            print("  -", llave)

        print()


if __name__ == "__main__":
    main()