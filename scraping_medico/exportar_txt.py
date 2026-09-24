import json
from pathlib import Path

entrada = Path("informes_500.json")
datos = json.loads(entrada.read_text(encoding="utf-8"))

carpeta = Path("informes_exportados")
carpeta.mkdir(exist_ok=True)

for informe in datos["informes"]:
    identificador = str(informe["id"])

    if not identificador.isdigit():
        raise ValueError("Identificador de informe inválido.")

    nombre = f"caso_{identificador}"

    (carpeta / f"{nombre}.txt").write_text(
        informe["texto"] + "\n",
        encoding="utf-8",
    )

    (carpeta / f"{nombre}.html").write_text(
        informe["html"],
        encoding="utf-8",
    )

print(f"Exportados {len(datos['informes'])} informes en {carpeta.resolve()}")