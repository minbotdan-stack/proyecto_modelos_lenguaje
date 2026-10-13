from pathlib import Path
import json
import re


BASE_DIR = Path(__file__).resolve().parent.parent

#CARPETA_ENTRADA = BASE_DIR / "originales" / "muestras"
CARPETA_ENTRADA = BASE_DIR / "originales" / "muestras_de_transcripciones"
#CARPETA_SALIDA = BASE_DIR / "resultados" / "secciones_prueba_v3"
CARPETA_SALIDA = BASE_DIR / "resultados" / "salida_100_transcripciones"
CARPETA_V2 = BASE_DIR / "resultados" / "secciones_prueba_v2"

CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)




PATRON_ENCABEZADO = re.compile(
    r"(?<![A-Za-z0-9])"
    r"("
    r"(?:Axis\s+[IVX]+)"
    r"|(?:A/P)"
    r"|(?:A|P)"
    r"|(?:[A-Z][A-Z0-9 /&().,'’+\-–—#]{1,60})"
    r"|(?:[A-Z][A-Z0-9]{1,}[a-z]+)"
    r"|(?:[A-Z][a-z]+(?:[ /][A-Z][a-z]+){0,3})"   # NUEVO: Title Case
    r")"
    r":(?=\s|$)"
)


def normalizar_saltos(texto):
    return texto.replace("\r\n", "\n").replace("\r", "\n")


def encontrar_encabezados(linea):
    """
    Devuelve los encabezados estructuralmente plausibles de una linea.

    Solo se acepta:
    - el primer encabezado si comienza la linea (ignorando espacios);
    - un encabezado posterior si:
        a) aparece inmediatamente despues de otro encabezado, o
        b) el texto anterior termina en puntuacion de cierre, o
        c) es un encabezado del tipo Axis I / Axis II / ...
    """
    encontrados = []

    for coincidencia in PATRON_ENCABEZADO.finditer(linea):
        if not encontrados:
            if linea[:coincidencia.start()].strip() == "":
                encontrados.append(coincidencia)
            continue

        anterior = encontrados[-1]
        texto_entre = linea[anterior.end():coincidencia.start()]
        etiqueta = coincidencia.group(1).strip()

        if (
            texto_entre.strip() == ""
            or re.search(r"[.!?]\s*$", texto_entre.strip())
            or re.fullmatch(r"Axis\s+[IVX]+", etiqueta)
        ):
            encontrados.append(coincidencia)

    return encontrados


def etiqueta_al_inicio(linea):
    encontrados = encontrar_encabezados(linea)
    if encontrados and linea[:encontrados[0].start()].strip() == "":
        return encontrados[0].group(1).strip()
    return None


def familia_etiqueta(etiqueta):
    """
    Permite reconocer continuaciones como:
        Axis I
        Axis II
        Axis III
    """
    coincidencia = re.match(r"^([A-Za-z]+)\s+", etiqueta)
    if coincidencia:
        return coincidencia.group(1).lower()
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

        # En muchos MTSamples "Medical Specialty:" aparece vacio
        # y el valor esta en la siguiente linea.
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


def agregar_valor(diccionario, llave, valor):
    """
    Evita perder informacion si una misma llave aparece mas de una vez.
    """
    if llave not in diccionario:
        diccionario[llave] = valor
        return

    existente = diccionario[llave]

    if isinstance(existente, list):
        existente.append(valor)
    else:
        diccionario[llave] = [existente, valor]


def agregar_texto(diccionario, llave, texto):
    """
    Agrega texto adicional a una seccion ya existente.
    """
    texto = texto.strip()

    if not texto:
        return

    if llave not in diccionario:
        diccionario[llave] = texto
        return

    existente = diccionario[llave]

    if isinstance(existente, str):
        if existente.strip():
            diccionario[llave] = existente + "\n" + texto
        else:
            diccionario[llave] = texto

    elif isinstance(existente, dict):
        if "__text__" in existente:
            existente["__text__"] += "\n" + texto
        else:
            existente["__text__"] = texto

    elif isinstance(existente, list):
        existente.append(texto)


def reconstruir_texto_json(objeto):
    """
    Reconstruye una representacion textual del JSON para comprobar
    que el contenido del TXT no se haya perdido durante la extraccion.

    No pretende reconstruir exactamente los saltos de linea originales;
    compara el contenido ignorando diferencias de espacios/saltos.
    """
    lineas = []

    if isinstance(objeto, dict):
        for llave, valor in objeto.items():

            # REPORT es un contenedor tecnico para texto sin encabezado.
            if llave == "REPORT":
                if isinstance(valor, str):
                    lineas.append(valor)
                continue

            # __text__ conserva texto asociado a una seccion que tambien
            # contiene subencabezados.
            if llave == "__text__":
                if isinstance(valor, str):
                    lineas.append(valor)
                continue

            if isinstance(valor, dict):
                lineas.append(f"{llave}:")
                lineas.extend(reconstruir_texto_json(valor))

            elif isinstance(valor, list):
                for elemento in valor:
                    if isinstance(elemento, (dict, list)):
                        lineas.append(f"{llave}:")
                        lineas.extend(reconstruir_texto_json(elemento))
                    else:
                        lineas.append(f"{llave}: {elemento}")

            else:
                lineas.append(f"{llave}: {valor}")

    elif isinstance(objeto, list):
        for elemento in objeto:
            lineas.extend(reconstruir_texto_json(elemento))

    return lineas


def normalizar_para_comparar(texto):
    """
    Normaliza solo espacios y elimina el marcador fijo del reporte.
    No modifica el contenido semantico.
    """
    texto = texto.replace(
        "(Medical Transcription Sample Report)",
        ""
    )
    return re.sub(r"\s+", " ", texto).strip()


def verificar_cobertura(ruta_txt, resultado):
    """
    Comprueba que el texto reconstruido desde el JSON conserve
    todos los tokens del TXT original, ignorando solo espacios.
    """
    texto_original = ruta_txt.read_text(encoding="utf-8")
    texto_reconstruido = "\n".join(
        reconstruir_texto_json(resultado)
    )

    original_normalizado = normalizar_para_comparar(
        texto_original
    )
    reconstruido_normalizado = normalizar_para_comparar(
        texto_reconstruido
    )

    return original_normalizado == reconstruido_normalizado


# ---------------------------------------------------------------
# NUEVO: alertas de calidad
# ---------------------------------------------------------------

# Una "Palabra:" que aparece dentro de un valor, despues de un
# punto o de un salto de linea, probablemente es un encabezado
# que no se separo.
PATRON_ENCABEZADO_SOSPECHOSO = re.compile(
    r"(?:^|\n|[.!?]\s+)([A-Z][A-Za-z/]*(?: [A-Za-z/]+){0,3}):(?=\s|$)"
)


def revisar_valores(objeto, ruta=""):
    """
    Devuelve una lista de (ruta, sospecha) para valores de texto que
    contienen algo parecido a un encabezado sin separar.
    """
    alertas = []

    if isinstance(objeto, dict):
        for llave, valor in objeto.items():
            alertas.extend(
                revisar_valores(valor, f"{ruta}/{llave}" if ruta else llave)
            )

    elif isinstance(objeto, list):
        for i, elemento in enumerate(objeto):
            alertas.extend(revisar_valores(elemento, f"{ruta}[{i}]"))

    elif isinstance(objeto, str):
        for coincidencia in PATRON_ENCABEZADO_SOSPECHOSO.finditer(objeto):
            alertas.append((ruta, coincidencia.group(1)))

    return alertas


def comparar_con_v2(nombre, resultado):
    """
    Compara las llaves de nivel superior (y de segundo nivel) contra
    el JSON de v2, si existe. Solo informa, no modifica nada.
    """
    ruta_v2 = CARPETA_V2 / f"{nombre}.json"

    if not ruta_v2.exists():
        print("  (sin JSON v2 para comparar)")
        return

    anterior = json.loads(ruta_v2.read_text(encoding="utf-8"))

    def aplanar(obj):
        llaves = set()
        for k, v in obj.items():
            llaves.add(k)
            if isinstance(v, dict):
                for k2 in v:
                    llaves.add(f"{k}/{k2}")
        return llaves

    llaves_v2 = aplanar(anterior)
    llaves_v3 = aplanar(resultado)

    nuevas = sorted(llaves_v3 - llaves_v2)
    perdidas = sorted(llaves_v2 - llaves_v3)

    if not nuevas and not perdidas:
        print("  Llaves vs v2: IGUALES")
        return

    print("  Llaves vs v2: CAMBIARON")
    for k in nuevas:
        print("    + nueva en v3:", k)
    for k in perdidas:
        print("    - ya no esta en v3:", k)


# ---------------------------------------------------------------


def es_seccion_contenedora(lineas, indice, encabezados):
    """
    Decide si una seccion debe representarse como objeto anidado.

    Evidencia estructural:
    1. Hay mas de un encabezado en la misma linea:
         PHYSICAL EXAMINATION: VITAL SIGNS: ...
    2. El encabezado esta vacio y la siguiente linea comienza
       con otro encabezado:
         MENTAL STATUS EXAM:
         GENERAL: ...
    """
    primero = encabezados[0]
    contenido = lineas[indice][primero.end():].strip()

    if len(encabezados) > 1:
        return True

    if not contenido and indice + 1 < len(lineas):
        return etiqueta_al_inicio(lineas[indice + 1]) is not None

    return False


def debe_ser_hijo(lineas, indice, etiqueta, ultimo_hijo):
    """
    Decide si un encabezado pertenece a la seccion contenedora actual.

    Reglas estructurales:
    - si no hay linea en blanco antes, normalmente continua el bloque;
    - si es una continuacion de familia (Axis I, II, III...), continua;
    - si la siguiente linea es otro encabezado, puede formar parte del
      mismo bloque aunque haya una linea en blanco antes.

    La decision NO depende del significado clinico del encabezado.
    """
    if ultimo_hijo is None:
        # Primer hijo despues del encabezado padre.
        if indice == 0:
            return False

        if not lineas[indice - 1].strip():
            return (
                indice + 1 < len(lineas)
                and etiqueta_al_inicio(lineas[indice + 1]) is not None
            )

        return True

    # Continuacion de familias como Axis I, Axis II, Axis III...
    familia_actual = familia_etiqueta(etiqueta)
    familia_anterior = familia_etiqueta(ultimo_hijo)

    if familia_actual and familia_actual == familia_anterior:
        return True

    # Si no hay linea en blanco, normalmente seguimos dentro del padre.
    if indice > 0 and lineas[indice - 1].strip():
        return True

    # Si despues viene inmediatamente otro encabezado, probablemente
    # seguimos dentro del bloque anidado.
    if indice + 1 < len(lineas):
        if etiqueta_al_inicio(lineas[indice + 1]) is not None:
            return True

    return False


def convertir_txt(ruta_txt):
    texto_original = ruta_txt.read_text(encoding="utf-8")
    texto = normalizar_saltos(texto_original)

    lineas = texto.splitlines()

    resultado = extraer_metadatos(lineas)

    # Localizar el inicio real del reporte.
    inicio = 0

    for i, linea in enumerate(lineas):
        if linea.strip().lower() == "(medical transcription sample report)":
            inicio = i + 1
            break

    cuerpo = lineas[inicio:]

    seccion_actual = None
    seccion_padre = None
    ultimo_hijo = None
    ultima_llave_top = None

    for indice, linea in enumerate(cuerpo):
        encabezados = encontrar_encabezados(linea)

        if not encabezados:
            if not linea.strip():
                continue

            texto = linea.strip()

            if seccion_padre is not None and ultimo_hijo is not None:
                agregar_texto(seccion_padre, ultimo_hijo, texto)

            elif ultima_llave_top is not None:
                agregar_texto(resultado, ultima_llave_top, texto)

            else:
                # Texto antes del primer encabezado.
                agregar_texto(resultado, "REPORT", texto)

            continue

        # La primera coincidencia debe estar al inicio de la linea.
        primero = encabezados[0]

        if linea[:primero.start()].strip():
            texto = linea.strip()

            if seccion_padre is not None and ultimo_hijo is not None:
                agregar_texto(seccion_padre, ultimo_hijo, texto)

            elif ultima_llave_top is not None:
                agregar_texto(resultado, ultima_llave_top, texto)

            else:
                agregar_texto(resultado, "REPORT", texto)

            continue

        etiqueta_primera = primero.group(1).strip()

        es_hijo = (
            seccion_padre is not None
            and debe_ser_hijo(
                cuerpo,
                indice,
                etiqueta_primera,
                ultimo_hijo
            )
        )

        if es_hijo:
            contenedor = seccion_padre
        else:
            # Nueva seccion de nivel superior.
            seccion_actual = {}
            seccion_padre = None
            ultimo_hijo = None
            ultima_llave_top = etiqueta_primera

            # Primero vemos si esta seccion tiene estructura anidada.
            contenedora = es_seccion_contenedora(
                cuerpo,
                indice,
                encabezados
            )

            if contenedora:
                resultado[etiqueta_primera] = {}
                seccion_actual = resultado[etiqueta_primera]
                seccion_padre = seccion_actual
                contenedor = seccion_padre
            else:
                # Seccion normal: su valor es texto, no un objeto vacio.
                pos_fin = (
                    encabezados[1].start()
                    if len(encabezados) > 1
                    else len(linea)
                )

                contenido = linea[primero.end():pos_fin].strip()

                resultado[etiqueta_primera] = contenido
                contenedor = None

        for posicion, encabezado in enumerate(encabezados):
            etiqueta = encabezado.group(1).strip()

            fin_contenido = (
                encabezados[posicion + 1].start()
                if posicion + 1 < len(encabezados)
                else len(linea)
            )

            contenido = linea[encabezado.end():fin_contenido].strip()

            if posicion == 0:
                if es_hijo:
                    agregar_valor(contenedor, etiqueta, contenido)
                    ultimo_hijo = etiqueta

                elif seccion_padre is not None:
                    # Ya fue creada como contenedora.
                    if contenido:
                        agregar_texto(
                            seccion_padre,
                            "__text__",
                            contenido
                        )

                else:
                    # Ya se guardo como valor simple arriba.
                    pass

            else:
                # Un segundo encabezado en la misma linea es una
                # subestructura del bloque actual.
                if es_hijo:
                    agregar_valor(contenedor, etiqueta, contenido)
                    ultimo_hijo = etiqueta
                else:
                    # La primera etiqueta es el padre top-level.
                    # Se creo como objeto por tener subencabezados.
                    if seccion_padre is not None:
                        agregar_valor(
                            seccion_padre,
                            etiqueta,
                            contenido
                        )
                        ultimo_hijo = etiqueta

        # Si la primera seccion era contenedora y no habia hijos aun,
        # la dejamos activa para las lineas siguientes.
        if not es_hijo and seccion_padre is not None:
            ultimo_hijo = (
                encabezados[-1].group(1).strip()
                if len(encabezados) > 1
                else None
            )

    return resultado


def main():
    archivos = sorted(CARPETA_ENTRADA.glob("*.txt"))

    if not archivos:
        print("No se encontraron archivos TXT.")
        return

    # Muestra de prueba.
    archivos_prueba = archivos

    print("Archivos encontrados:", len(archivos))
    print("Archivos de prueba:", len(archivos_prueba))
    print("Salida:", CARPETA_SALIDA)
    print()

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

        cobertura = verificar_cobertura(
            ruta_txt,
            resultado
        )

        print(
            "Cobertura de contenido:",
            "CORRECTA" if cobertura else "REVISAR"
        )

        print("Llaves detectadas:")

        for llave in resultado:
            print("  -", llave)

        # Comparacion con v2
        comparar_con_v2(ruta_txt.stem, resultado)

        # Alertas de posibles encabezados dentro de valores
        alertas = revisar_valores(resultado)

        for ruta_valor, sospecha in alertas:
            print(f"  ALERTA: '{sospecha}:' dentro de {ruta_valor}")

        print()


if __name__ == "__main__":
    main()