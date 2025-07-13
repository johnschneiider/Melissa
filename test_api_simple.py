import requests

# Probar la API
url = "http://127.0.0.1:8000/clientes/api/buscar-negocios/"
params = {"ubicacion": "Cali"}

try:
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    if response.status_code == 200:
        data = response.json()
        print(f"Negocios encontrados: {data.get('total_resultados', 0)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}") 