import requests
import time

def test_rate_limiting():
    """Script para probar el rate limiting"""
    base_url = "http://127.0.0.1:8000"
    test_url = f"{base_url}/cuentas/test-rate-limit/"
    
    print("🧪 Probando Rate Limiting...")
    print("=" * 50)
    
    # Hacer 15 peticiones rápidas (el límite es 10 por minuto)
    for i in range(15):
        try:
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Petición {i+1}: Exitosa (200)")
            elif response.status_code == 429:
                print(f"🚫 Petición {i+1}: Rate Limited (429) - ¡Rate limiting funciona!")
            else:
                print(f"❓ Petición {i+1}: Código {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Petición {i+1}: Error - {e}")
        
        time.sleep(0.1)  # Pequeña pausa entre peticiones
    
    print("\n" + "=" * 50)
    print("✅ Prueba completada. Si viste códigos 429, el rate limiting está funcionando.")

if __name__ == "__main__":
    test_rate_limiting() 