#!/usr/bin/env python
"""
Script de prueba para verificar la API de búsqueda de negocios
"""
import requests
import json

def test_api_busqueda():
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: Búsqueda por ubicación con coordenadas
    print("=== Test 1: Búsqueda por coordenadas ===")
    params = {
        'lat': '3.4516',
        'lon': '-76.5320',
        'radio': '500'
    }
    
    try:
        response = requests.get(f"{base_url}/clientes/api/buscar-negocios/", params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Negocios encontrados: {data.get('total_resultados', 0)}")
            print(f"Parámetros: {data.get('parametros_busqueda', {})}")
            for negocio in data.get('negocios', [])[:3]:  # Mostrar solo los primeros 3
                print(f"- {negocio.get('nombre')} ({negocio.get('direccion')})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error en test 1: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Búsqueda por ubicación textual
    print("=== Test 2: Búsqueda por ubicación textual ===")
    params = {
        'ubicacion': 'Cali'
    }
    
    try:
        response = requests.get(f"{base_url}/clientes/api/buscar-negocios/", params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Negocios encontrados: {data.get('total_resultados', 0)}")
            print(f"Parámetros: {data.get('parametros_busqueda', {})}")
            for negocio in data.get('negocios', [])[:3]:
                print(f"- {negocio.get('nombre')} ({negocio.get('direccion')})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error en test 2: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Búsqueda por servicio
    print("=== Test 3: Búsqueda por servicio ===")
    params = {
        'servicio': 'corte'
    }
    
    try:
        response = requests.get(f"{base_url}/clientes/api/buscar-negocios/", params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Negocios encontrados: {data.get('total_resultados', 0)}")
            print(f"Parámetros: {data.get('parametros_busqueda', {})}")
            for negocio in data.get('negocios', [])[:3]:
                print(f"- {negocio.get('nombre')} ({negocio.get('direccion')})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error en test 3: {e}")

if __name__ == "__main__":
    test_api_busqueda() 