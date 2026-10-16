import json
import ollama

MODELO = 'qwen2.5:14b'
MIN_INFORMES = 2           
TAM_LOTE = 20

IGNORAR = {"SAMPLE NAME", "MEDICAL SPECIALTY", "DESCRIPTION", "MS"} 

with open("plantilla_cribada.json", encoding="utf-8") as f:
    plantilla = json.load(f)
with open("conteo.json", encoding="utf-8") as f:
    inv = json.load(f)
with open("mapeo_abreviaturas.json", encoding="utf-8") as f:
    abrev = json.load(f)


def campos(d, pref=""):
    """Entrega solo los campos finales (hojas) que son texto, no listas."""
    for k, v in d.items():
        ruta = f"{pref}.{k}" if pref else k
        if isinstance(v, dict):
            yield from campos(v, ruta)
        elif isinstance(v, str):
            yield ruta


CAMPOS = list(campos(plantilla))

DESCRIPCIONES = {
    "subjective.history.medications": "medications the patient ALREADY takes (home/current/outpatient)",
    "plan.medications_prescribed": "NEW prescriptions or medications to start/continue as part of the plan",
    "subjective.review_of_systems": "symptom review by system, as reported by the patient (denies/negative for...)",
    "objective.physical_exam.general": "general appearance and overall exam findings by the clinician",
    "objective.studies_and_procedures": "imaging, EKG, echo, endoscopy, procedures and their results",
    "objective.laboratory": "blood/urine lab values",
    "assessment.diagnoses": "impression, assessment, diagnoses, problem lists",
    "assessment.clinical_comments": "discussion, reasoning, summary",
    "assessment.hospital_course": "narrative of what happened during hospital/ER stay",
    "plan.treatment_and_recommendations": "plan, recommendations, treatment, goals",
}

claves = [c for c, d in inv.items()
          if c.upper() not in IGNORAR and d["conteo"] >= MIN_INFORMES]
print(len(claves), "claves a asignar;", len(CAMPOS), "campos")

lista_campos = [{"campo": c, "descripcion": DESCRIPCIONES.get(c, "")} for c in CAMPOS]

prompt = f"""You are a clinical documentation expert. Each item is a section heading from an
English medical report ("nombre" is the heading, expanded if it was an abbreviation), with
example content. Assign it to exactly ONE field from this closed list, or "none" if no
field fits:
{json.dumps(lista_campos)}
Rules:
- Choose only a "campo" value from the list, or "none".
- Decide using the example content, not only the heading.
- Reply ONLY with JSON: {{"asignaciones": [{{"clave": "...", "campo": "..."}}]}}"""

asignadas = {}
for i in range(0, len(claves), TAM_LOTE):
    lote = [{"clave": c,
             "nombre": abrev.get(c, c).replace("_", " "),
             "ejemplos": [e[:120] for e in inv[c]["ejemplos"][:2]]}
            for c in claves[i:i + TAM_LOTE]]
    r = ollama.chat(
        model=MODELO,
        messages=[{'role': 'system', 'content': prompt},
                  {'role': 'user', 'content': json.dumps(lote, ensure_ascii=False)}],
        format='json',
        options={'temperature': 0, 'num_ctx': 8192})
    try:
        items = json.loads(r['message']['content']).get("asignaciones", [])
    except json.JSONDecodeError:
        print("Lote inválido:", i)
        continue
    for m in items:
        if m.get("clave") in inv and (m.get("campo") in CAMPOS or m.get("campo") == "none"):
            asignadas[m["clave"]] = m["campo"]
    print(f"Procesadas {min(i + TAM_LOTE, len(claves))} de {len(claves)}")
    with open("mapeo_campos.json", "w", encoding="utf-8") as f:   # guardado parcial
        json.dump(asignadas, f, indent=2, ensure_ascii=False)

perdidas = [c for c in claves if c not in asignadas]

total = sum(inv[c]["conteo"] for c in claves)
cubierto = sum(inv[c]["conteo"] for c, campo in asignadas.items() if campo != "none")
print(f"\nAsignadas a un campo: {sum(1 for v in asignadas.values() if v != 'none')} de {len(claves)}")
print(f"Marcadas 'none': {sum(1 for v in asignadas.values() if v == 'none')}")
print(f"Sin respuesta del modelo: {len(perdidas)}")
print(f"Cobertura ponderada: {100 * cubierto / total:.1f}%")

por_campo = {}
for c in claves:
    campo = asignadas.get(c, "SIN_RESPUESTA")
    por_campo.setdefault(campo, []).append((inv[c]["conteo"], c))
revision = {k: [f"{n}  {c}" for n, c in sorted(v, reverse=True)[:25]]
            for k, v in sorted(por_campo.items())}

with open("revision_por_campo.json", "w", encoding="utf-8") as f:
    json.dump(revision, f, indent=2, ensure_ascii=False)