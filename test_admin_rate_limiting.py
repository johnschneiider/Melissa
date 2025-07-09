#!/usr/bin/env python
"""
Script para probar la gestión de rate limiting desde el admin
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melissa.settings')
django.setup()

from cuentas.models import RateLimitConfig

def test_rate_limiting_admin():
    """Probar la funcionalidad de gestión de rate limiting"""
    print("🧪 Probando Gestión de Rate Limiting...")
    print("=" * 50)
    
    # Verificar configuraciones existentes
    configs = RateLimitConfig.objects.all()
    print(f"📊 Total configuraciones: {configs.count()}")
    
    for config in configs:
        status = "✅ ACTIVO" if config.activo else "❌ INACTIVO"
        print(f"   {config.nombre}: {config.limite} - {status}")
    
    # Probar obtener configuración dinámica
    print("\n🔧 Probando configuraciones dinámicas:")
    test_configs = ['login_rate', 'register_rate', 'reservation_rate', 'test_rate']
    
    for clave in test_configs:
        valor = RateLimitConfig.get_config(clave, 'default')
        print(f"   {clave}: {valor}")
    
    # Probar obtener todas las configuraciones
    all_configs = RateLimitConfig.get_all_configs()
    print(f"\n📋 Todas las configuraciones activas: {len(all_configs)}")
    for clave, valor in all_configs.items():
        print(f"   {clave}: {valor}")
    
    print("\n✅ Prueba completada. Si ves las configuraciones, el sistema está funcionando.")

if __name__ == "__main__":
    test_rate_limiting_admin() 