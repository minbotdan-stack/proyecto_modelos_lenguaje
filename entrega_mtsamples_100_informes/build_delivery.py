from pathlib import Path
from hashlib import sha256
from collections import Counter
import json
import re
import statistics
import zipfile

ROOT = Path('/mnt/data')

def get_json(filename):
    return json.loads((ROOT / filename).read_text(encoding='utf-8'))

def dump_json(filename,obj):
    (ROOT / filename).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

ref_data=get_json('muestras_500.json')
full_data=get_json('transcripciones_405.json')
select=get_json('seleccion_100.json')
selected_data=get_json('transcripciones_100.json')
assert len(ref_data['registros'])==500 and len(full_data['registros'])==405
assert len(selected_data['registros'])==100
assert len(select['casos'])==100 and len({c['id'] for c in select['casos']})==100
assert set(c['id'] for c in select['casos'])==set(r['id'] for r in selected_data['registros'])
all_trans={r['id']:r for r in full_data['registros']}
assert len(all_trans)==405
assert len({r['id'] for r in ref_data['registros']})==500
assert all(sha256(r['texto_original'].encode('utf8')).hexdigest()==r['sha256'] for r in ref_data['registros'])
assert all(sha256(r['texto_original'].encode('utf8')).hexdigest()==r['sha256'] for r in full_data['registros'])
assert all(all_trans[r['id']]==r for r in selected_data['registros'])

report_dir=ROOT/'informes_100_txt'
report_dir.mkdir(exist_ok=True)
reports=[]
pairs=[]
metrics=[]
for trans in selected_data['registros']:
    ident=trans['id']
    raw=(ROOT/'generated_reports'/f'{ident}.txt').read_text(encoding='utf8')
    match=re.fullmatch(r'TITLE: ([^\n]+)\nDESCRIPTION: ([^\n]+)\n\n(.*)',raw,flags=re.S)
    if not match:
        raise ValueError(f'Formato invalido del borrador {ident}')
    title, description, body=match.groups()
    body=body.strip()
    if not body or len(body.split())<100:
        raise ValueError(f'Informe demasiado corto: {ident}')
    if '@@@' in body or 'PATIENT '+ident in body or 'DOCTOR '+ident in body:
        raise ValueError(f'Residuos de transcripcion en {ident}')
    doc=f'Sample Name: {title}\n\nMedical Specialty:\n\nConsult - History and Phy.\n\nDescription: {description}\n\n(Medical Transcription Sample Report)\n\n{body}\n'
    (report_dir/f'informe_{ident}.txt').write_text(doc,encoding='utf8')
    report={'id':ident,'archivo':'informe_'+ident+'.txt','transcripcion_origen':trans['archivo'],'sha256_transcripcion':trans['sha256'],'sha256_informe':sha256(doc.encode('utf8')).hexdigest(),'titulo':title,'descripcion':description,'texto_generado':doc,'procedencia':'informe sintetico redactado por IA; no revisado por un medico'}
    reports.append(report)
    pairs.append({'id':ident,'texto_entrada':trans['texto_original'],'texto_salida':doc,'sha256_transcripcion':trans['sha256'],'sha256_informe':report['sha256_informe'],'etiqueta':'sintetica_generada_por_IA_sin_validacion_clinica'})
    metrics.append({'id':ident,'palabras_transcripcion':len(trans['texto_original'].split()),'palabras_informe':len(doc.split())})
assert len(reports)==100 and len(pairs)==100
assert len(list(report_dir.glob('*.txt')))==100
assert all(sha256((report_dir/r['archivo']).read_bytes()).hexdigest()==r['sha256_informe'] for r in reports)

report_filename='informes_generados_100.json'
pair_filename='pares_entrenamiento_100.json'
dump_json(report_filename,{'conjunto':'informes_generados','cantidad':100,'categoria_referencia':'Consult - History and Phy.','tipo_de_etiquetas':'sinteticas_generadas_por_IA','validacion_clinica':'pendiente','registros':reports})
dump_json(pair_filename,{'conjunto':'pares_transcripcion_informe','cantidad':100,'tipo_de_etiquetas':'sinteticas_generadas_por_IA','validacion_clinica':'pendiente','registros':pairs})
dump_json('metricas_generacion_100.json',{'cantidad':100,'mediana_palabras_transcripcion':statistics.median(x['palabras_transcripcion'] for x in metrics),'mediana_palabras_informe':statistics.median(x['palabras_informe'] for x in metrics),'registros':metrics})

# Reopen, cross-check round-trip and linkage.
generated_again=get_json(report_filename)
paired_again=get_json(pair_filename)
assert len(generated_again['registros'])==len(paired_again['registros'])==100
for a,b,c in zip(generated_again['registros'],paired_again['registros'],selected_data['registros']):
    assert a['id']==b['id']==c['id']
    assert a['texto_generado']==b['texto_salida']
    assert b['texto_entrada']==c['texto_original']
    assert a['sha256_transcripcion']==sha256(b['texto_entrada'].encode('utf8')).hexdigest()
    assert a['sha256_informe']==sha256(b['texto_salida'].encode('utf8')).hexdigest()

qrows='\n'.join(f"| {q['cuartil']} | {q['elegibles']} | {q['min_palabras']}–{q['max_palabras']} | {q['seleccionados']} |" for q in select['cuartiles'])
ids=', '.join(r['id'] for r in selected_data['registros'])
words=statistics.median(x['palabras_informe'] for x in metrics)
doc=f'''# Documentación metodológica de generación de informes

## 1. Objetivo y alcance

El objetivo de esta entrega es proporcionar **100 informes clínicos sintéticos en inglés** redactados a partir de **100 transcripciones médico-paciente** seleccionadas entre 405, tomando como **referencia descriptiva de estilo y organización** 500 informes de MTSamples, categoría *Consult - History and Phy.*. No se ha impuesto un número fijo de secciones: los encabezados usados dependen del contenido del caso. El texto clínico debe interpretarse como una **etiqueta sintética propuesta**, no como un informe original de MTSamples ni como un registro verificado por personal sanitario.

## 2. Fuentes

- `muestras_500.json`: 500 referencias originales, preservadas sin cambios.
- `transcripciones_405.json`: 405 transcripciones de origen, preservadas sin cambios.
- Los JSON usan `id`, `archivo`, `sha256` y `texto_original` como campos de origen. Los SHA-256 fueron contrastados con los bytes UTF-8 de cada campo textual.

## 3. Muestreo reproducible de las 100 transcripciones

**Población inicial:** 405 transcripciones. **Exclusiones provisionales para esta primera selección:** 12 identificadores detectados durante una inspección estructural previa y pendientes de aclaración: {', '.join(select['excluidos'])}. No se borraron ni descartaron del conjunto original de 405. **Población elegible:** 393.

1. Ordenar los casos elegibles por número de palabras (`len(texto_original.split())`); desempatar por identificador alfabético.
2. Partir el orden en cuatro cuartiles por índice, usando límites `i*n//4`.
3. Seleccionar sin reemplazo 25 casos de cada cuartil mediante Python `random.Random(42).sample`.
4. Ordenar los 100 seleccionados por ID. El archivo `seleccion_100.json` conserva las cantidades, intervalos y los SHA-256 seleccionados.

| Cuartil | Elegibles | Palabras en la transcripción | Seleccionados |
|---|---:|---:|---:|
{qrows}

**IDs seleccionados:** {ids}.

La estratificación por longitud favorece cobertura de diferentes tamaños de conversación; **no constituye una muestra probabilística irrestricta de los 405** por la exclusión de 12 casos, ni asegura representatividad de diagnósticos, especialidades, edad o gravedad.

## 4. Criterios de generación

- Leer la transcripción de cada encuentro y distinguir información del paciente, antecedentes, examen, tratamientos, recomendaciones, órdenes y decisiones finales.
- Redactar en inglés médico narrativo parecido a MTSamples, usando únicamente encabezados clínicamente sustentados por el texto. No usar una plantilla universal de 23 apartados ni trasladar mecánicamente todos los metadatos de audio a la nota.
- Resumir diálogos informales, sin añadir edad, sexo, fecha, hallazgos normales, diagnósticos definitivos, dosis de medicamentos o resultados de pruebas que no estén respaldados por la conversación.
- Diferenciar los fármacos habituales, las propuestas discutidas, los cambios establecidos en las instrucciones finales y las pruebas meramente consideradas.
- Evitar interpretar los fragmentos `@@@` como información recuperable; los originales se preservan intactos en el JSON de entradas.
- El encabezado del informe adopta las convenciones visuales `Sample Name`, `Medical Specialty`, `Description` y `(Medical Transcription Sample Report)`. Esto **no indica** procedencia original de MTSamples: la procedencia real consta en los metadatos y en esta documentación.

## 5. Archivos de entrega

- `informes_generados_100.json`: 100 documentos sintéticos en `texto_generado`, con ID, origen, título, descripción, hash de entrada y de salida y advertencia de procedencia.
- `informes_100_txt/informe_ID.txt`: un TXT por cada informe sintético.
- `transcripciones_100.json`: los 100 textos originales completos para revisión.
- `pares_entrenamiento_100.json`: `texto_entrada` (diálogo original) y `texto_salida` (nota generada) con sus identificadores; útil para preparar *fine-tuning* supervisado tras curación.
- `seleccion_100.json`: registro de selección reproducible.
- `metricas_generacion_100.json`: longitudes de entrada y salida.
- `muestras_500.json` y `transcripciones_405.json`: conjuntos fuente originales.
- `prepare_selection.py` y `build_delivery.py`: scripts para reproducir la **selección y el ensamblaje de la entrega**. La redacción de las notas se realizó con un modelo lingüístico y revisión contextual dentro de la conversación; **estos scripts por sí solos NO regeneran la redacción de las 100 notas**. Se conservan los borradores intermedios en `generated_reports/` para auditoría.

## 6. Verificaciones automáticas completadas

- 500 referencias, 405 transcripciones originales, 100 transcripciones seleccionadas, 100 informes y 100 pares.
- Unicidad de los identificadores de la selección y coincidencia con sus originales.
- Comprobación byte por byte del texto original, mediante su codificación UTF-8 y SHA-256, y comprobación SHA-256 de los 100 informes finales.
- Correspondencia del mismo ID entre informe, transcripción y par de entrenamiento, incluyendo igualdad de `texto_salida`.
- Comprobación de que la nota generada no contiene el marcador `@@@` ni el identificador de interlocutor del archivo.
- Mediana de longitud de los informes generados: {words} palabras, calculada con `split` y **no** un tokenizador de modelo.

Estas verificaciones comprueban **integridad, formato y correspondencia entre archivos**, no exactitud clínica de las notas. No se ha realizado revisión humana por un médico, evaluación ciega ni verificación exhaustiva de afirmaciones contra cada fragmento de diálogo.

## 7. Limitaciones y validación clínica pendiente

**No tratar las 100 notas como referencia de oro (*gold standard*)**. Las notas sintéticas pueden contener omisiones, relaciones causales incorrectas, interpretaciones no seguras, errores de dosis y alucinaciones. Antes de su empleo en entrenamiento o evaluación clínica, se recomienda inspección de **los 100 casos por al menos un revisor clínico competente**, señalando para cada dato su soporte textual, estado de certidumbre, completitud y fidelidad de las recomendaciones finales. Marcar y corregir discrepancias en una versión derivada controlada, dejando el archivo entregado como punto de partida auditado. Evitar usar las mismas transcripciones, paciente o información clínica cercana en entrenamiento y evaluación para prevenir fuga de datos.

Los 500 MTSamples son **referencias de estilo clínico**, no pares supervisados conversación→nota. Los 100 pares sí aportan entradas y etiquetas, pero son etiquetas generadas. No se verificaron licencias de redistribución ni ausencia total de datos identificables en fuentes; corresponde comprobar permisos de uso, confidencialidad, políticas institucionales y privacidad antes de compartir o entrenar modelos con estos datos.
'''
(ROOT/'documentacion_generacion.md').write_text(doc,encoding='utf8')

# One compact delivery archive, with originals included for reproducibility.
archive=ROOT/'entrega_mtsamples_100_informes.zip'
includes=['muestras_500.json','transcripciones_405.json','transcripciones_100.json','seleccion_100.json','informes_generados_100.json','pares_entrenamiento_100.json','metricas_generacion_100.json','documentacion_generacion.md','prepare_selection.py','build_delivery.py']
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
    for name in includes: z.write(ROOT/name,arcname=name)
    for file in sorted(report_dir.glob('*.txt')):z.write(file,arcname='informes_100_txt/'+file.name)
    for file in sorted((ROOT/'generated_reports').glob('*.txt')):z.write(file,arcname='generated_reports/'+file.name)
with zipfile.ZipFile(archive) as z:
    bad=z.testzip()
    assert bad is None,bad
    assert len(z.namelist())==210,len(z.namelist())
print('VALIDACION_FINAL: CORRECTA')
print('ORIGINALES: MTSamples',len(ref_data['registros']),'TRANSCRIPCIONES',len(full_data['registros']))
print('TRANSCRIPCIONES_SELECCIONADAS',len(selected_data['registros']))
print('INFORMES',len(reports),'PARES',len(pairs),'TXT',len(list(report_dir.glob('*.txt'))))
print('MEDIANA_PALABRAS_INFORMES',words)
print('ARCHIVO_ZIP',archive,archive.stat().st_size)
print('ZIP_ENTRADAS',len(z.namelist()),'TEST_ZIP: OK')
