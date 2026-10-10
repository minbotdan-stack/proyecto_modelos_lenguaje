# Documentación metodológica de generación de informes

## Objetivo y alcance

El objetivo de esta entrega es proporcionar **100 informes clínicos sintéticos en inglés** redactados a partir de **100 transcripciones médico-paciente** seleccionadas entre 405, tomando como **referencia descriptiva de estilo y organización** 500 informes de MTSamples, categoría *Consult - History and Phy.*. No se ha impuesto un número fijo de secciones: los encabezados usados dependen del contenido del caso. El texto clínico debe interpretarse como una **etiqueta sintética propuesta**, no como un informe original de MTSamples ni como un registro verificado por personal sanitario.

## Fuentes

- `muestras_500.json`: 500 referencias originales, preservadas sin cambios.
- `transcripciones_405.json`: 405 transcripciones de origen, preservadas sin cambios.
- Los JSON usan `id`, `archivo`, `sha256` y `texto_original` como campos de origen. Los SHA-256 fueron contrastados con los bytes UTF-8 de cada campo textual.

## Muestreo reproducible de las 100 transcripciones

**Población inicial:** 405 transcripciones. **Exclusiones provisionales para esta primera selección:** 12 identificadores detectados durante una inspección estructural previa y pendientes de aclaración: A723, D107, E231, E862, H279, H617, L179, M178, M243, P829, S614, V472. No se borraron ni descartaron del conjunto original de 405. **Población elegible:** 393.

1. Ordenar los casos elegibles por número de palabras (`len(texto_original.split())`); desempatar por identificador alfabético.
2. Partir el orden en cuatro cuartiles por índice, usando límites `i*n//4`.
3. Seleccionar sin reemplazo 25 casos de cada cuartil mediante Python `random.Random(42).sample`.
4. Ordenar los 100 seleccionados por ID. El archivo `seleccion_100.json` conserva las cantidades, intervalos y los SHA-256 seleccionados.

| Cuartil | Elegibles | Palabras en la transcripción | Seleccionados |
|---|---:|---:|---:|
| 1 | 98 | 831–2400 | 25 |
| 2 | 98 | 2409–3430 | 25 |
| 3 | 98 | 3434–4382 | 25 |
| 4 | 99 | 4395–13125 | 25 |

**IDs seleccionados:** A320, A843, B311, B610, C013, C332, C353, C602, D009, D030, D106, D322, D346, D557, E143, E376, E463, E484, E485, E704, E988, F017, F064, F237, F276, F815, F948, G436, G479, H199, H349, H507, H986, I163, I377, I546, I780, I907, J087, J277, J539, J764, K223, K343, K413, K664, K673, L144, L610, L682, L929, M017, M191, N112, N198, N303, N372, N655, N685, O005, O313, O603, P330, Q111, Q133, Q175, Q561, Q755, Q997, R458, R642, S027, S363, S459, S463, S967, T380, T497, T606, T665, V282, V469, V623, V773, W204, W253, W915, X026, X607, X745, X848, X885, Y336, Y471, Y768, Z075, Z166, Z196, Z293, Z641.

La estratificación por longitud favorece cobertura de diferentes tamaños de conversación; **no constituye una muestra probabilística irrestricta de los 405** por la exclusión de 12 casos, ni asegura representatividad de diagnósticos, especialidades, edad o gravedad.

## Criterios de generación

- Leer la transcripción de cada encuentro y distinguir información del paciente, antecedentes, examen, tratamientos, recomendaciones, órdenes y decisiones finales.
- Redactar en inglés médico narrativo parecido a MTSamples, usando únicamente encabezados clínicamente sustentados por el texto. No usar una plantilla universal de 23 apartados ni trasladar mecánicamente todos los metadatos de audio a la nota.
- Resumir diálogos informales, sin añadir edad, sexo, fecha, hallazgos normales, diagnósticos definitivos, dosis de medicamentos o resultados de pruebas que no estén respaldados por la conversación.
- Diferenciar los fármacos habituales, las propuestas discutidas, los cambios establecidos en las instrucciones finales y las pruebas meramente consideradas.
- Evitar interpretar los fragmentos `@@@` como información recuperable; los originales se preservan intactos en el JSON de entradas.
- El encabezado del informe adopta las convenciones visuales `Sample Name`, `Medical Specialty`, `Description` y `(Medical Transcription Sample Report)`. Esto **no indica** procedencia original de MTSamples: la procedencia real consta en los metadatos y en esta documentación.

## Archivos de entrega

- `informes_generados_100.json`: 100 documentos sintéticos en `texto_generado`, con ID, origen, título, descripción, hash de entrada y de salida y advertencia de procedencia.
- `informes_100_txt/informe_ID.txt`: un TXT por cada informe sintético.
- `transcripciones_100.json`: los 100 textos originales completos para revisión.
- `pares_entrenamiento_100.json`: `texto_entrada` (diálogo original) y `texto_salida` (nota generada) con sus identificadores; útil para preparar *fine-tuning* supervisado tras curación.
- `seleccion_100.json`: registro de selección reproducible.
- `metricas_generacion_100.json`: longitudes de entrada y salida.
- `muestras_500.json` y `transcripciones_405.json`: conjuntos fuente originales.
- `prepare_selection.py` y `build_delivery.py`: scripts para reproducir la **selección y el ensamblaje de la entrega**. La redacción de las notas se realizó con un modelo lingüístico y revisión contextual dentro de la conversación; **estos scripts por sí solos NO regeneran la redacción de las 100 notas**. Se conservan los borradores intermedios en `generated_reports/` para auditoría.

## Verificaciones automáticas completadas

- 500 referencias, 405 transcripciones originales, 100 transcripciones seleccionadas, 100 informes y 100 pares.
- Unicidad de los identificadores de la selección y coincidencia con sus originales.
- Comprobación byte por byte del texto original, mediante su codificación UTF-8 y SHA-256, y comprobación SHA-256 de los 100 informes finales.
- Correspondencia del mismo ID entre informe, transcripción y par de entrenamiento, incluyendo igualdad de `texto_salida`.
- Comprobación de que la nota generada no contiene el marcador `@@@` ni el identificador de interlocutor del archivo.
- Mediana de longitud de los informes generados: 291.0 palabras, calculada con `split` y **no** un tokenizador de modelo.


