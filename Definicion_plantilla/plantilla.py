import json
import re
import ollama

MODELO = 'qwen2.5:14b'
MIN_INFORMES = 5
IGNORAR = {"SAMPLE NAME", "MEDICAL SPECIALTY", "DESCRIPTION"}

with open("conteo.json", encoding="utf-8") as f:
    inv = json.load(f)
with open("mapeo_abreviaturas.json", encoding="utf-8") as f:
    abrev = json.load(f)

def norm(k):
    return re.sub(r"\s+", " ", k.strip().upper())

conteos, ejemplo = {}, {}
for clave, d in inv.items():
    k = norm(clave)
    if k in IGNORAR:
        continue
    nombre = abrev.get(k, abrev.get(clave, k)).replace("_", " ").upper()
    conteos[nombre] = conteos.get(nombre, 0) + d["conteo"]
    if nombre not in ejemplo and d["ejemplos"]:
        ejemplo[nombre] = d["ejemplos"][0][:70]

frecuentes = sorted(((n, c) for n, c in conteos.items() if c >= MIN_INFORMES),
                    key=lambda x: -x[1])
lista = "\n".join(f"{c} | {n} | {ejemplo.get(n, '')}" for n, c in frecuentes)
print("Claves que se envían al modelo:", len(frecuentes))

prompt = """You are an expert in clinical documentation and data structuring.
You receive section headings from 500 English medical reports, in the format
"reports_containing_it | heading | example text".
Design ONE general report template in JSON.
Rules:
-The top level MUST be exactly: "subjective", "objective", "assessment", "plan".
-Inside each, create fields (snake_case, English, values ""), merging headings that
   mean the same thing. Group physical-exam systems under objective.physical_exam.
-Only create fields supported by the list. Do not invent sections.
-Aim for 25 to 40 fields in total.
Reply ONLY with the JSON template."""

r = ollama.chat(
    model=MODELO,
    messages=[{'role': 'system', 'content': prompt},
              {'role': 'user', 'content': lista}],
    format='json',
    options={'temperature': 0, 'num_ctx': 16384})

plantilla = json.loads(r['message']['content'])
with open("plantilla_modelo.json", "w", encoding="utf-8") as f:
    json.dump(plantilla, f, indent=2, ensure_ascii=False)
print(json.dumps(plantilla, indent=2, ensure_ascii=False))