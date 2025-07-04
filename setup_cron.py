#!/usr/bin/env python3
"""
Script para configurar cron jobs para los recordatorios de Melissa
"""

import os
import sys
from pathlib import Path

def crear_cron_jobs():
    """Crea los cron jobs para los recordatorios"""
    
    # Obtener la ruta del proyecto
    proyecto_path = Path(__file__).parent.absolute()
    manage_py_path = proyecto_path / "manage.py"
    
    # Verificar que manage.py existe
    if not manage_py_path.exists():
        print("❌ Error: No se encontró manage.py en el directorio actual")
        return False
    
    # Crear el contenido del cron job
    cron_content = f"""# Cron jobs para recordatorios de Melissa
# Ejecutar cada hora para verificar recordatorios de 3 horas
0 * * * * cd {proyecto_path} && python manage.py enviar_recordatorios --tipo tres_horas >> logs/recordatorios.log 2>&1

# Ejecutar diariamente a las 9:00 AM para recordatorios de 1 día
0 9 * * * cd {proyecto_path} && python manage.py enviar_recordatorios --tipo dia_antes >> logs/recordatorios.log 2>&1
"""
    
    # Crear directorio de logs si no existe
    logs_dir = proyecto_path / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Crear archivo de cron
    cron_file = proyecto_path / "melissa_cron.txt"
    with open(cron_file, 'w', encoding='utf-8') as f:
        f.write(cron_content)
    
    print("✅ Archivo de cron jobs creado exitosamente!")
    print(f"📁 Ubicación: {cron_file}")
    print("\n📋 Para instalar los cron jobs, ejecuta:")
    print(f"crontab {cron_file}")
    print("\n📋 Para ver los cron jobs actuales:")
    print("crontab -l")
    print("\n📋 Para editar los cron jobs manualmente:")
    print("crontab -e")
    
    return True

def mostrar_instrucciones_windows():
    """Muestra instrucciones para Windows Task Scheduler"""
    
    print("\n🪟 INSTRUCCIONES PARA WINDOWS:")
    print("1. Abre 'Programador de tareas' (Task Scheduler)")
    print("2. Crea una nueva tarea básica")
    print("3. Configura las siguientes tareas:")
    print("\n   📅 Tarea 1 - Recordatorios de 3 horas:")
    print("   - Frecuencia: Cada hora")
    print("   - Acción: Iniciar programa")
    print("   - Programa: python")
    print("   - Argumentos: manage.py enviar_recordatorios --tipo tres_horas")
    print("   - Iniciar en: [ruta_del_proyecto]")
    print("\n   📅 Tarea 2 - Recordatorios de 1 día:")
    print("   - Frecuencia: Diariamente a las 9:00 AM")
    print("   - Acción: Iniciar programa")
    print("   - Programa: python")
    print("   - Argumentos: manage.py enviar_recordatorios --tipo dia_antes")
    print("   - Iniciar en: [ruta_del_proyecto]")

def main():
    """Función principal"""
    
    print("🚀 Configurando cron jobs para recordatorios de Melissa")
    print("=" * 60)
    
    # Detectar sistema operativo
    if os.name == 'nt':  # Windows
        print("🪟 Detectado Windows")
        mostrar_instrucciones_windows()
    else:  # Linux/Mac
        print("🐧 Detectado Linux/Mac")
        crear_cron_jobs()
    
    print("\n" + "=" * 60)
    print("✅ Configuración completada!")
    print("\n📝 NOTAS IMPORTANTES:")
    print("• Asegúrate de que el servidor de email esté configurado en settings.py")
    print("• Los logs se guardarán en logs/recordatorios.log")
    print("• Puedes probar manualmente con: python manage.py enviar_recordatorios")
    print("• Para ver logs en tiempo real: tail -f logs/recordatorios.log")

if __name__ == "__main__":
    main() 