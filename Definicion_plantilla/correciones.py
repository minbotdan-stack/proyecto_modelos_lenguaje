import json

with open("mapeo_campos.json", encoding="utf-8") as f:
    mapeo = json.load(f)
with open("conteo.json", encoding="utf-8") as f:
    inv = json.load(f)

H = "subjective.history."
E = "objective.physical_exam."

CORRECCIONES = {
    "DESCRIPTION": "none",
    "REASON FOR CONSULTATION": "subjective.chief_complaint",
    "REASON FOR CONSULT": "subjective.chief_complaint",
    "REASON FOR THE CONSULT": "subjective.chief_complaint",
    "REASON FOR REFERRAL": "subjective.chief_complaint",
    "REASON FOR ADMISSION": "subjective.chief_complaint",
    "ASSESSMENT AND PLAN": "assessment.assessment_and_plan",
    "ASSESSMENT/PLAN": "assessment.assessment_and_plan",
    "IMPRESSION AND PLAN": "assessment.assessment_and_plan",
    "IMPRESSION/PLAN": "assessment.assessment_and_plan",
    "A/P": "assessment.assessment_and_plan",
    "OBSTETRICAL HISTORY": H + "obstetric_gynecologic",
    "GYN HISTORY": H + "obstetric_gynecologic",
    "OB HISTORY": H + "obstetric_gynecologic",
    "GYN": H + "obstetric_gynecologic",
    "BIRTH HISTORY": H + "developmental_birth",
    "DEVELOPMENTAL HISTORY": H + "developmental_birth",
    "DEVELOPMENTAL": H + "developmental_birth",
    "MEDS": H + "medications",
    "FORMULATION": "assessment.clinical_comments",
    "MAJOR FINDINGS": E + "general",
    "OTOSCOPY": E + "heent",
    "ORAL CAVITY": E + "heent",
    "GAIT": E + "neurological",
    "STATION/GAIT": E + "neurological",
    "COORD": E + "neurological",
    "BREASTS": E + "genitourinary",
    "TESTS ORDERED": "plan.studies_ordered",
    "ESTIMATED LENGTH OF STAY": "plan.disposition",
    "CONDITION UPON DISPOSITION": "plan.disposition",
    "IDENTIFYING DATA": "subjective.history_of_present_illness",
    "RELEVANT BACKGROUND INFORMATION": "subjective.history_of_present_illness",
    "LEGAL HISTORY": H + "social_history",
    "EMPLOYER": H + "social_history",
    "TRAVEL HISTORY": H + "social_history",
    "ENDOCRINE": "subjective.review_of_systems",
    "OBJECTIVE": "none",
}
mapeo.update(CORRECCIONES)

META = {"SAMPLE NAME", "MEDICAL SPECIALTY", "DESCRIPTION"}
claves = [c for c, d in inv.items() if c not in META and d["conteo"] >= 2]
total = sum(inv[c]["conteo"] for c in claves)
en_campo = sum(inv[c]["conteo"] for c in claves if mapeo.get(c, "none") != "none")
print(f"Cobertura real en campos de la plantilla: {100 * en_campo / total:.1f}%")

with open("mapeo_campos.json", "w", encoding="utf-8") as f:
    json.dump(mapeo, f, indent=2, ensure_ascii=False)