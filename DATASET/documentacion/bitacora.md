# Bitácora de preparación de conjuntos de datos

## Etapa 1. Organización inicial

**Sistema operativo:** Zorin OS (Linux).

**Proyecto:** Preparación de conjuntos de datos para el procesamiento de transcripciones médico-paciente mediante modelos de lenguaje.

### 1. Conjuntos de datos

Se dispone de dos conjuntos de datos independientes:

- **Dataset A:** 500 informes médicos de MTSamples, correspondientes a la categoría *Consult - History and Phy.*
- **Dataset B:** 405 transcripciones de conversaciones médico-paciente.

Ambos conjuntos se encuentran almacenados originalmente en archivos de texto plano (TXT).

**Total:** 905 archivos TXT.

### 2. Organización de directorios

Se utiliza un directorio principal denominado `DATASET`, organizado mediante las siguientes carpetas:

- `originales/muestras`: almacenamiento de los 500 informes médicos.
- `originales/transcripciones`: almacenamiento de las 405 transcripciones.
- `scripts`: programas de procesamiento de datos.
- `resultados`: archivos generados durante el procesamiento.
- `documentacion`: registro de procedimientos y verificaciones.

### 3. Verificación inicial

Mediante la terminal Bash de Zorin OS se ejecutaron los siguientes comandos:

```bash
find originales/muestras -maxdepth 1 -type f -name "*.txt" | wc -l

find originales/transcripciones -maxdepth 1 -type f -name "*.txt" | wc -l
```

**Resultados obtenidos:**

- Informes médicos: 500.
- Transcripciones médicas: 405.
- Total: 905 archivos.

### 4. Resultado de la etapa

La verificación inicial confirmó que ambos directorios contienen las cantidades esperadas de archivos TXT.

Esta comprobación no garantiza todavía la integridad del contenido, la codificación, la ausencia de archivos vacíos o la inexistencia de duplicados.

Estas características serán evaluadas durante la siguiente etapa, antes de realizar la conversión a JSON.



## Etapa 2. Validación de integridad y calidad de los archivos

**Objetivo:** Evaluar las características básicas de los 905 archivos TXT antes de su conversión a formato JSON.

**Herramientas utilizadas:**
- Sistema operativo Zorin OS.
- Python 3.
- Visual Studio Code.
- Bibliotecas estándar de Python: `pathlib`, `collections`, `hashlib` y `csv`.

**Procedimiento:**

Se desarrolló el script `validar_txt.py` para recorrer los dos conjuntos de datos, verificar sus cantidades, identificar archivos vacíos, comprobar la compatibilidad con las codificaciones UTF-8 y Windows-1252, detectar caracteres nulos y calcular una huella digital SHA-256 para cada archivo.

Las huellas permiten identificar archivos cuyo contenido binario es idéntico.

Los resultados individuales se almacenan en `validacion_archivos.csv` para su revisión y documentación.

El procedimiento es de solo lectura respecto a los datos originales.

**Resultados de ejecución:** Pendientes de registrar.

**Observaciones:** La comprobación realizada constituye una validación inicial. No garantiza por sí misma que las transcripciones estén completas, que todos los caracteres se hayan interpretado correctamente ni que los archivos no presenten duplicación parcial.

### Resultados de la validación

Se ejecutó el script `validar_txt.py` sobre los dos conjuntos de datos, obteniéndose los siguientes resultados:

| Indicador | Resultado |
|---|---:|
| Informes médicos analizados | 500 |
| Transcripciones analizadas | 405 |
| Total de archivos | 905 |
| Archivos con estado OK | 905 |
| Archivos compatibles con UTF-8 | 905 |
| Grupos de duplicados exactos (SHA-256) | 0 |
| Archivos con problemas detectados | 0 |

**Archivo de resultados:** `resultados/validacion_archivos.csv`.

La validación confirmó que los 905 archivos superaron las comprobaciones técnicas iniciales. Todos pudieron decodificarse mediante UTF-8, no se identificaron archivos vacíos o sin texto útil, no se detectaron caracteres nulos y no se encontraron contenidos binarios idénticos según las huellas SHA-256 calculadas.

Estos resultados permiten continuar con la inspección de contenido y estructura. No obstante, la validación no garantiza la completitud semántica de los documentos ni la ausencia de duplicados parciales.




## Etapa 3. Inspección estructural de los conjuntos de datos

**Objetivo:** Identificar las características estructurales de los informes clínicos de referencia y las transcripciones médicas originales.

**Procedimiento:**

Se desarrolló el script `inspeccionar_estructura.py` para analizar los 905 archivos TXT mediante expresiones regulares y búsqueda de patrones textuales.

En el conjunto MTSamples se verificó la presencia de los campos `Sample Name`, `Medical Specialty`, `Description` y el encabezado identificador del informe clínico.

En las transcripciones se analizaron los metadatos del encuentro, las intervenciones del médico y del paciente, la correspondencia entre los identificadores internos y los nombres de archivo, así como los marcadores de segmentos incomprensibles (`@@@`).

Los resultados individuales se almacenan en `resultados/inspeccion_estructura.csv`.

El procedimiento no modifica los archivos originales ni realiza normalización o eliminación de contenido.

**Resultados:** Pendientes de ejecución y verificación.




### Resultados de la inspección estructural

Se ejecutó el script `inspeccionar_estructura.py` sobre los 905 archivos TXT de ambos conjuntos de datos.

**Resultados del conjunto MTSamples:**

- Informes analizados: 500.
- Informes sin observaciones estructurales: 500.
- Informes señalados para revisión: 0.

**Resultados del conjunto de transcripciones:**

- Transcripciones analizadas: 405.
- Transcripciones sin observaciones: 393.
- Transcripciones señaladas para revisión: 12.
- Apariciones del marcador `@@@`: 16,172.

Las 12 transcripciones señaladas presentan diferencias en la detección de fechas, horas, identificadores o etiquetas de participantes. Estas observaciones no necesariamente representan errores en los archivos, por lo que requieren una revisión adicional.

Se estableció un procedimiento de inspección mediante Bash para examinar los encabezados y los identificadores presentes en dichos archivos.

Los resultados de esta revisión se almacenan en `resultados/revision_12.txt`.

**Estado:** Revisión de las 12 transcripciones pendiente de interpretación.

**Criterio metodológico:** Los archivos originales se conservarán sin modificaciones. Las posibles inconsistencias se documentarán antes de efectuar la transformación a JSON.




### Revisión de anomalías estructurales

De las 405 transcripciones analizadas, 12 fueron señaladas por el procedimiento de inspección estructural.

La revisión manual de sus encabezados permitió identificar cinco archivos con diferencias en la representación de metadatos o etiquetas de participantes: D107, E231, L179, M243 y P829.

Adicionalmente, siete archivos contenían identificadores de participantes distintos del identificador asociado al nombre del archivo: A723, E862, H279, H617, M178, S614 y V472.

Se estableció una revisión contextual de estos últimos para determinar si corresponden a intervenciones adicionales, diferencias de transcripción o posibles fragmentos mezclados.

No se realizaron modificaciones ni exclusiones de los datos originales. La decisión sobre su tratamiento queda pendiente de la revisión contextual.




### Conclusión de la inspección estructural

La inspección de los 905 documentos identificó 12 transcripciones con diferencias estructurales. Cinco presentaron variaciones en la representación de metadatos o participantes, mientras que siete contenían identificadores adicionales o diferentes de los asociados al archivo.

La revisión contextual mostró cambios tanto puntuales como persistentes en los identificadores. No se encontraron evidencias suficientes, en los fragmentos examinados, para confirmar la mezcla de encuentros clínicos.

Se decidió preservar íntegramente los 905 archivos originales y mantener documentadas las 12 observaciones para su posterior revisión durante la preparación del conjunto de entrenamiento.

La conversión inicial a JSON se realizará sin correcciones ni normalización del contenido original.


## Etapa 4. Conversión de archivos TXT a JSON

**Objetivo:** Transformar los 500 informes médicos de referencia y las 405 transcripciones médico-paciente desde archivos TXT a un formato JSON estructurado, preservando la información original.

**Herramientas:** Python 3 y bibliotecas estándar `pathlib`, `hashlib` y `json`.

**Procedimiento:**

Se desarrolló el script `convertir_json.py`, encargado de recorrer ambos conjuntos de datos y generar un registro JSON por cada archivo TXT.

Cada registro incluye el identificador original, el nombre del archivo, su huella SHA-256 y el contenido textual completo.

Para evitar alteraciones, los archivos se leyeron directamente como bytes y se decodificaron mediante UTF-8 sin eliminar caracteres ni normalizar saltos de línea.

Posteriormente se implementó una validación de ida y vuelta, consistente en recuperar el contenido desde JSON, codificarlo nuevamente a UTF-8 y compararlo byte por byte con el archivo TXT correspondiente.

**Archivos de salida:**

- `resultados/muestras_500.json`
- `resultados/transcripciones_405.json`

**Resultados de la conversión y validación:** Pendientes de ejecución.




### Resultados de la conversión TXT a JSON

La ejecución del script `convertir_json.py` finalizó correctamente.

Se generaron dos archivos:

`muestras_500.json` 2.3 MB 
`transcripciones_405.json` 8.1 MB

El programa comprobó la cantidad de registros de cada conjunto y realizó una verificación de ida y vuelta. El texto recuperado desde cada registro JSON fue codificado nuevamente en UTF-8 y comparado byte por byte con el archivo TXT correspondiente. También se verificaron las huellas SHA-256.

Las verificaciones finalizaron satisfactoriamente en ambos conjuntos de datos.

Se conservaron todos los documentos, incluidos aquellos que presentaban diferencias estructurales identificadas durante la inspección anterior.


