import json,random,re,hashlib,collections,statistics,pathlib
ROOT=pathlib.Path('/mnt/data')
refs=json.loads((ROOT/'muestras_500.json').read_text(encoding='utf8'))['registros']
trans=json.loads((ROOT/'transcripciones_405.json').read_text(encoding='utf8'))['registros']
excludes={'A723','D107','E231','E862','H279','H617','L179','M178','M243','P829','S614','V472'}
pool=sorted([r for r in trans if r['id'] not in excludes],key=lambda r:(len(r['texto_original'].split()),r['id']))
assert len(pool)==393
quartile=[]
for i in range(4):quartile.append(pool[i*len(pool)//4:(i+1)*len(pool)//4])
rng=random.Random(42); selected=[]; table=[]
for i,q in enumerate(quartile):
 picks=rng.sample(q,25)
 table.append((i+1,len(q),min(len(t['texto_original'].split()) for t in q),max(len(t['texto_original'].split()) for t in q)))
 for p in picks:selected.append((i+1,p))
selected.sort(key=lambda x:x[1]['id'])
print('quartiles',table,'selected',len(selected));print('selection list:')
for group, r in selected:print(group,r['id'],len(r['texto_original'].split()))
obj={'metodo':'Muestreo estratificado por cuartil de palabras de las transcripciones (conteo split), sin reemplazo, random.Random(42); 25 por cuartil. Exclusión provisional de 12 archivos con observaciones estructurales para revisión pendiente.','semilla':42,'poblacion':405,'excluidos':sorted(excludes),'elegibles':len(pool),'seleccionados':len(selected),'cuartiles':[{'cuartil':q,'elegibles':n,'min_palabras':lo,'max_palabras':hi,'seleccionados':25} for q,n,lo,hi in table],'casos':[{'id':r['id'],'archivo':r['archivo'],'cuartil':group,'palabras':len(r['texto_original'].split()),'sha256':r['sha256']} for group,r in selected]}
(ROOT/'seleccion_100.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'transcripciones_100.json').write_text(json.dumps({'conjunto':'transcripciones','cantidad':100,'origen':'transcripciones_405.json','seleccion':'seleccion_100.json','registros':[r for q,r in selected]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
