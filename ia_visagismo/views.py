from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
import requests
from .models import AnalisisVisagismo, RecomendacionCorte, HistorialVisagismo
from .services import VisagismoService, IAImageProcessor, ReplicateService
from threading import Thread
from django.conf import settings
import logging

@login_required
def visagismo_home(request):
    """Página principal del visagismo"""
    analisis_recientes = AnalisisVisagismo.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')[:5]
    
    return render(request, 'ia_visagismo/home.html', {
        'analisis_recientes': analisis_recientes
    })

@login_required
def subir_foto(request):
    """Vista para subir foto y iniciar análisis"""
    if request.method == 'POST':
        if 'imagen' not in request.FILES:
            messages.error(request, 'Por favor selecciona una imagen')
            return redirect('ia_visagismo:subir_foto')
        
        imagen = request.FILES['imagen']
        
        # Validar tipo de archivo
        if not imagen.content_type.startswith('image/'):
            messages.error(request, 'Por favor sube una imagen válida')
            return redirect('ia_visagismo:subir_foto')
        
        # Crear análisis
        analisis = AnalisisVisagismo.objects.create(
            usuario=request.user,
            imagen_original=imagen,
            estado='pendiente'
        )
        
        # Iniciar procesamiento en background
        thread = Thread(target=procesar_analisis_background, args=(analisis.id,))
        thread.start()
        
        messages.success(request, 'Imagen subida correctamente. El análisis comenzará en breve.')
        return redirect('ia_visagismo:resultado', analisis_id=analisis.id)
    
    return render(request, 'ia_visagismo/subir_foto.html')

def procesar_analisis_background(analisis_id):
    """Procesa el análisis en background"""
    try:
        analisis = AnalisisVisagismo.objects.get(id=analisis_id)
        analisis.estado = 'procesando'
        analisis.save()
        
        # Procesar imagen
        imagen_path = analisis.imagen_original.path
        imagen_procesada_path = IAImageProcessor.procesar_imagen(imagen_path)
        
        # Analizar con IA
        servicio = VisagismoService()
        caracteristicas = servicio.analizar_rostro(imagen_procesada_path)
        
        if 'error' in caracteristicas:
            analisis.estado = 'error'
            analisis.save()
            return
        
        # Generar recomendaciones
        recomendaciones = servicio.generar_recomendaciones(caracteristicas)
        
        # Actualizar análisis
        analisis.forma_cara = caracteristicas.get('forma_cara', '')
        analisis.medidas_faciales = caracteristicas.get('medidas_faciales', {})
        analisis.recomendaciones = recomendaciones
        analisis.estado = 'completado'
        
        # Guardar imagen procesada
        if os.path.exists(imagen_procesada_path):
            with open(imagen_procesada_path, 'rb') as f:
                analisis.imagen_procesada.save(
                    f'procesada_{os.path.basename(imagen_procesada_path)}',
                    ContentFile(f.read())
                )
        
        analisis.save()
        
        # Crear recomendaciones en base de datos y generar imagen automáticamente
        replicate_service = ReplicateService()
        for rec in recomendaciones:
            corte = RecomendacionCorte.objects.create(
                analisis=analisis,
                nombre_corte=rec['nombre'],
                descripcion=rec['descripcion'],
                categoria=rec['categoria'],
                confianza=rec['confianza']
            )
            # Generar imagen con Replicate
            try:
                prompt_corte = rec.get('prompt', '')
                if prompt_corte:
                    imagen_generada_url = replicate_service.generar_imagen_con_corte(
                        analisis.imagen_original.path,
                        prompt_corte
                    )
                    if imagen_generada_url:
                        response = requests.get(imagen_generada_url, timeout=60)
                        if response.status_code == 200:
                            nombre_archivo = f"generada_{corte.id}_{os.path.basename(analisis.imagen_original.name)}"
                            corte.imagen_ejemplo.save(nombre_archivo, ContentFile(response.content))
                            corte.save()
            except Exception as e:
                print(f"Error generando imagen para corte {corte.nombre_corte}: {e}")
        
        # Limpiar archivo temporal
        if os.path.exists(imagen_procesada_path):
            os.remove(imagen_procesada_path)
            
    except Exception as e:
        print(f"Error procesando análisis {analisis_id}: {e}")
        try:
            analisis = AnalisisVisagismo.objects.get(id=analisis_id)
            analisis.estado = 'error'
            analisis.save()
        except:
            pass

@login_required
def resultado_analisis(request, analisis_id):
    """Muestra el resultado del análisis"""
    analisis = get_object_or_404(AnalisisVisagismo, id=analisis_id, usuario=request.user)
    cortes_recomendados = RecomendacionCorte.objects.filter(analisis=analisis, activo=True)
    # Multiplicar confianza por 100 para mostrar como porcentaje
    for corte in cortes_recomendados:
        corte.confianza = corte.confianza * 100
    return render(request, 'ia_visagismo/resultado.html', {
        'analisis': analisis,
        'cortes_recomendados': cortes_recomendados
    })

@login_required
def historial_visagismo(request):
    """Muestra el historial de consultas"""
    historial = HistorialVisagismo.objects.filter(
        usuario=request.user
    ).order_by('-fecha_consulta')
    
    return render(request, 'ia_visagismo/historial.html', {
        'historial': historial
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def guardar_seleccion(request):
    """Guarda la selección del usuario"""
    try:
        data = json.loads(request.body)
        analisis_id = data.get('analisis_id')
        corte_id = data.get('corte_id')
        satisfaccion = data.get('satisfaccion')
        comentarios = data.get('comentarios', '')
        
        analisis = get_object_or_404(AnalisisVisagismo, id=analisis_id, usuario=request.user)
        corte = get_object_or_404(RecomendacionCorte, id=corte_id, analisis=analisis)
        
        # Crear o actualizar historial
        historial, created = HistorialVisagismo.objects.get_or_create(
            usuario=request.user,
            analisis=analisis,
            defaults={
                'corte_seleccionado': corte,
                'satisfaccion': satisfaccion,
                'comentarios': comentarios
            }
        )
        
        if not created:
            historial.corte_seleccionado = corte
            historial.satisfaccion = satisfaccion
            historial.comentarios = comentarios
            historial.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def api_estado_analisis(request, analisis_id):
    """API para verificar el estado del análisis"""
    analisis = get_object_or_404(AnalisisVisagismo, id=analisis_id, usuario=request.user)
    
    return JsonResponse({
        'estado': analisis.estado,
        'completado': analisis.estado == 'completado'
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def generar_imagen_corte(request):
    """Genera una imagen con el corte aplicado usando Replicate (síncrono, AJAX)"""
    try:
        data = json.loads(request.body)
        analisis_id = data.get('analisis_id')
        corte_id = data.get('corte_id')
        logging.info(f"[Visagismo] Solicitud de generación de imagen: analisis_id={analisis_id}, corte_id={corte_id}")
        analisis = get_object_or_404(AnalisisVisagismo, id=analisis_id, usuario=request.user)
        corte = get_object_or_404(RecomendacionCorte, id=corte_id, analisis=analisis)
        recomendaciones = analisis.recomendaciones
        prompt_corte = None
        for rec in recomendaciones:
            if rec['nombre'] == corte.nombre_corte:
                prompt_corte = rec.get('prompt', '')
                break
        if not prompt_corte:
            logging.error("[Visagismo] No se encontró el prompt para este corte")
            return JsonResponse({'error': 'No se encontró el prompt para este corte'}, status=400)
        replicate_service = ReplicateService()
        logging.info(f"[Visagismo] Llamando a Replicate con prompt: {prompt_corte}")
        imagen_generada_url = replicate_service.generar_imagen_con_corte(
            analisis.imagen_original.path,
            prompt_corte
        )
        logging.info(f"[Visagismo] URL de imagen generada: {imagen_generada_url}")
        if imagen_generada_url:
            try:
                response = requests.get(imagen_generada_url, timeout=60)
                if response.status_code == 200:
                    nombre_archivo = f"generada_{corte.id}_{os.path.basename(analisis.imagen_original.name)}"
                    corte.imagen_ejemplo.save(nombre_archivo, ContentFile(response.content))
                    corte.save()
                    logging.info(f"[Visagismo] Imagen guardada correctamente: {corte.imagen_ejemplo.url}")
                    return JsonResponse({'success': True, 'imagen_url': corte.imagen_ejemplo.url})
                else:
                    logging.error(f"[Visagismo] Error al descargar la imagen generada: status_code={response.status_code}")
                    return JsonResponse({'error': 'No se pudo descargar la imagen generada'}, status=500)
            except Exception as e:
                logging.error(f"[Visagismo] Error al descargar la imagen generada: {e}")
                return JsonResponse({'error': f'Error al descargar la imagen generada: {e}'}, status=500)
        else:
            logging.error("[Visagismo] No se pudo generar la imagen (Replicate no devolvió URL)")
            return JsonResponse({'error': 'No se pudo generar la imagen'}, status=500)
    except Exception as e:
        logging.error(f"[Visagismo] Error inesperado: {e}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def estado_tarea_generar_imagen(request, task_id):
    """Devuelve el estado y resultado de la tarea de generación de imagen"""
    result = AsyncResult(task_id)
    if result.state == 'SUCCESS':
        return JsonResponse({'state': result.state, 'imagen_url': result.result})
    return JsonResponse({'state': result.state})
