import json
import ollama

USAR_MODELO = True       # pon True para pedirle sugerencias al modelo
MODELO = 'qwen2.5:14b'

ABREV = {
    "cc": "chief_complaint", "hpi": "history_of_present_illness",
    "pmh": "past_medical_history", "ros": "review_of_systems",
    "meds": "medications", "pe": "physical_exam",
}

MANUAL = {
    "A": "assessment", "P": "plan", "A/P": "assessment_and_plan",
    "PE": "physical_exam", "PEX": "physical_exam",
    "FEN": "fluids_electrolytes_nutrition",
    "ADD": "near_addition", "OD": "right_eye", "OS": "left_eye",
    "WT": "weight", "HT": "height", "VS": "vital_signs",
    "PPH": "past_psychiatric_history", "ENMT": "ears_nose_mouth_throat",
    "CN": "cranial_nerves", "COR": "cardiovascular", "CV": "cardiovascular",
    "CVS": "cardiovascular", "GU": "genitourinary", "GI": "gastrointestinal",
    "ENT": "ears_nose_throat", "FHX": "family_history", "SHX": "social_history",
    "PSH": "past_surgical_history", "HX": "history_of_present_illness",
    "FH": "family_history", "SOCH": "social_history",
    "CXR": "chest_xray", "EKG": "ekg", "ECHO": "echocardiogram",
    "EEG": "eeg", "TEE": "transesophageal_echo",
    "MSE": "mental_status_exam", "RX": "prescriptions",
    # "MS" se deja fuera por su uso amiguo como "musculoskeletal" y "multiple sclerosis"
}

PALABRAS = {"NECK", "BACK", "HEAD", "SKIN", "HEART", "NOSE", "EARS", "EAR", "EYES",
            "EYE", "DIET", "GAIT", "PLAN", "LABS", "LAB", "DATA", "STUDY", "BONE",
            "HIPS", "HIP", "FOOT", "KNEE", "ANKLE", "WRIST", "ELBOW", "MOUTH",
            "ANUS", "COURSE", "GENERAL", "OTHER", "STAGE", "GOALS", "QUESTION",
            "ANSWER", "REASON", "REPORT", "FINDINGS"}

with open("conteo.json", encoding="utf-8") as f:
    inv = json.load(f)

mapeo = {}
ambiguas = []

for clave, d in inv.items():
    h = clave.lower()
    if h in ABREV:
        mapeo[clave] = ABREV[h]
    elif clave in MANUAL:
        pass                                   # se aplica al final
    elif len(clave) <= 4 and clave not in PALABRAS:
        ambiguas.append((clave, d))

mapeo.update(MANUAL)                           # lo manual siempre gana
ambiguas = [(c, d) for c, d in ambiguas if c not in mapeo]

print(len(mapeo), "resueltas por reglas/manual")
print(len(ambiguas), "siglas sin resolver:", [c for c, _ in ambiguas])

sugerencias = []
if USAR_MODELO and ambiguas:
    prompt = """You are a clinical documentation expert. The keys are section headings
from English-language medical transcription reports, probably abbreviations.
For each key, propose the most likely full English heading in snake_case.
Rules:
- "evidencia" must be copied VERBATIM from that key's own "ejemplos". If "ejemplos"
  is empty, evidencia must be "" and confianza must be "baja".
- If you are not sure, use "ambiguo".
Reply ONLY with JSON:
{"mapeo": [{"clave": "...", "significado": "...", "evidencia": "...", "confianza": "alta|media|baja"}]}"""

    por_mayus = {c.upper(): c for c, _ in ambiguas}
    for i in range(0, len(ambiguas), 15):
        lote = [{"clave": c, "ejemplos": d["ejemplos"],
                 "hermanas": list(d["hermanas"])[:6]}
                for c, d in ambiguas[i:i + 15]]
        r = ollama.chat(
            model=MODELO,
            messages=[{'role': 'system', 'content': prompt},
                      {'role': 'user', 'content': json.dumps(lote, ensure_ascii=False)}],
            format='json',
            options={'temperature': 0, 'num_ctx': 8192})
        try:
            items = json.loads(r['message']['content']).get("mapeo", [])
        except json.JSONDecodeError:
            print("Respuesta inválida en el lote", i)
            continue
        for m in items:
            original = por_mayus.get(str(m.get("clave", "")).upper())
            if original:                       # descarta claves inventadas
                m["clave"] = original          # restaura mayúsculas
                sugerencias.append(m)

with open("mapeo_abreviaturas.json", "w", encoding="utf-8") as f:
    json.dump(mapeo, f, indent=2, ensure_ascii=False)
with open("sugerencias_modelo.json", "w", encoding="utf-8") as f:
    json.dump(sugerencias, f, indent=2, ensure_ascii=False)
with open("siglas_pendientes.json", "w", encoding="utf-8") as f:
    json.dump([c for c, _ in ambiguas], f, indent=2, ensure_ascii=False)