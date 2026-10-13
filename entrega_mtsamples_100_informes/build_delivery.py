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

print('Fin del algoritmo')