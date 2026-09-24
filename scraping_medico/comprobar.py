import requests

url = (
    "https://www.mtsamples.com/site/pages/browse.asp"
    "?type=97-Consult+%2D+History+and+Phy%2E"
)

respuesta = requests.get(url, timeout=30)

print("Código de respuesta:", respuesta.status_code)
print("Primeros 500 caracteres:")
print(respuesta.text[:500])

if respuesta.status_code == 200:
    with open("categoria.html", "w", encoding="utf-8") as archivo:
        archivo.write(respuesta.text)

    print("Página guardada en categoria.html")
else:
    print("No se pudo descargar el listado.")