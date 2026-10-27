import ollama    
import json  

# Cambia estas dos rutas por las tuyas
RUTA_TRANSCRIPCION = "/home/daniel/proyectos/pruebas/A320.txt"
RUTA_PLANTILLA = "/home/daniel/proyectos/pruebas/plantilla_final.json"

transcripcion = open(RUTA_TRANSCRIPCION, encoding="utf-8").read()
plantilla = open(RUTA_PLANTILLA, encoding="utf-8").read()

prompt = f"""You are a clinical information extractor. Your task is to extract clinical information from the following and fill out the provided JSON {plantilla} strictly adhering to its format.

Rules:
- Return ONLY one valid JSON object with exactly the same keys and nesting as the template. Do not add, remove or rename keys.
- Use only information explicitly stated in the transcript. Never invent diagnoses, doses, values or findings.
- If a field is not mentioned in the transcript, fill it with the string "Not specified by the patient".
- Write the values in concise clinical language.
- Markers such as @@@ mean unintelligible audio, ignore them.
- Put each piece of information in the single most appropriate field. Try not to repeat it in several fields.
"""

respuesta = ollama.chat(
    model="qwen2.5:14b",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": transcripcion},],
    format="json",
    options={"num_ctx": 16384, "temperature": 0},
)

resultado_json = json.loads(respuesta['message']['content'])
with open("/home/daniel/proyectos/pruebas/A320_resultado_2_5.json", "w", encoding="utf-8") as f:
    json.dump(resultado_json, f, indent=2, ensure_ascii=False)

print("JSON guardado correctamente.")