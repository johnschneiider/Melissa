from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Limpia logs antiguos y mantiene el sistema de logging optimizado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de días para mantener logs (default: 30)'
        )
        parser.add_argument(
            '--max-size',
            type=int,
            default=100,
            help='Tamaño máximo en MB para cada archivo de log (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin ejecutar la limpieza'
        )

    def handle(self, *args, **options):
        days = options['days']
        max_size_mb = options['max_size']
        dry_run = options['dry_run']
        
        # Obtener directorio de logs
        logs_dir = Path(settings.BASE_DIR) / 'logs'
        
        if not logs_dir.exists():
            self.stdout.write(
                self.style.WARNING(f'Directorio de logs no encontrado: {logs_dir}')
            )
            return
        
        # Archivos de log a procesar
        log_files = [
            'melissa_general.log',
            'melissa_errors.log',
            'melissa_security.log',
            'melissa_activity.log',
            'melissa_business.log',
            'melissa_recordatorios.log'
        ]
        
        total_size_before = 0
        total_size_after = 0
        files_processed = 0
        
        for log_file in log_files:
            log_path = logs_dir / log_file
            
            if not log_path.exists():
                continue
            
            # Obtener tamaño actual
            current_size = log_path.stat().st_size
            total_size_before += current_size
            
            self.stdout.write(f'\nProcesando: {log_file}')
            self.stdout.write(f'Tamaño actual: {current_size / (1024*1024):.2f} MB')
            
            # Verificar si excede el tamaño máximo
            if current_size > (max_size_mb * 1024 * 1024):
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f'  [DRY RUN] Se reduciría el tamaño de {log_file}')
                    )
                else:
                    try:
                        # Leer las últimas líneas y crear nuevo archivo
                        with open(log_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        # Mantener solo las últimas 1000 líneas
                        lines_to_keep = lines[-1000:] if len(lines) > 1000 else lines
                        
                        # Crear backup del archivo original
                        backup_path = log_path.with_suffix('.backup')
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                        
                        # Escribir nuevo archivo con líneas reducidas
                        with open(log_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines_to_keep)
                        
                        new_size = log_path.stat().st_size
                        total_size_after += new_size
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  Archivo reducido: {current_size / (1024*1024):.2f} MB → {new_size / (1024*1024):.2f} MB'
                            )
                        )
                        
                        # Eliminar backup después de 24 horas
                        import time
                        if backup_path.exists():
                            os.utime(backup_path, (time.time() - 86400, time.time() - 86400))
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  Error procesando {log_file}: {e}')
                        )
                        total_size_after += current_size
                files_processed += 1
            else:
                self.stdout.write(f'  Tamaño OK, no requiere limpieza')
                total_size_after += current_size
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN DE LIMPIEZA DE LOGS')
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY RUN - No se realizaron cambios')
            )
        
        self.stdout.write(f'Archivos procesados: {files_processed}')
        self.stdout.write(f'Tamaño total antes: {total_size_before / (1024*1024):.2f} MB')
        self.stdout.write(f'Tamaño total después: {total_size_after / (1024*1024):.2f} MB')
        
        if total_size_before > total_size_after:
            saved = total_size_before - total_size_after
            self.stdout.write(
                self.style.SUCCESS(f'Espacio liberado: {saved / (1024*1024):.2f} MB')
            )
        
        # Log de la actividad
        logger.info(
            f'Limpieza de logs completada: {files_processed} archivos procesados, '
            f'{total_size_before / (1024*1024):.2f} MB → {total_size_after / (1024*1024):.2f} MB'
        ) 