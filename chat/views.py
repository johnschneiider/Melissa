from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import Conversacion, Mensaje

User = get_user_model()

@login_required
def lista_conversaciones(request):
    """Vista para mostrar la lista de conversaciones del usuario"""
    # Obtener todas las conversaciones del usuario
    conversaciones = Conversacion.objects.filter(
        Q(participante1=request.user) | Q(participante2=request.user)
    ).annotate(
        ultimo_mensaje=Max('mensajes__timestamp')
    ).order_by('-ultimo_mensaje')
    
    # Preparar datos de conversaciones
    conversaciones_data = []
    for conv in conversaciones:
        # Determinar el otro participante
        otro_usuario = conv.participante2 if conv.participante1 == request.user else conv.participante1
        
        # Obtener el último mensaje
        ultimo_mensaje = conv.mensajes.order_by('-timestamp').first()
        
        # Contar mensajes no leídos
        mensajes_no_leidos = conv.mensajes.filter(
            remitente=otro_usuario,
            leido=False
        ).count()
        
        conversaciones_data.append({
            'conversacion': conv,
            'otro_usuario': otro_usuario,
            'ultimo_mensaje': ultimo_mensaje,
            'mensajes_no_leidos': mensajes_no_leidos
        })
    
    return render(request, 'chat/lista_conversaciones.html', {
        'conversaciones': conversaciones_data
    })

@login_required
def chat_individual(request, conversacion_id):
    """Vista para el chat individual con un usuario"""
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    
    # Verificar que el usuario es participante de la conversación
    if request.user not in [conversacion.participante1, conversacion.participante2]:
        return redirect('chat:lista_conversaciones')
    
    # Determinar el otro participante
    otro_usuario = conversacion.participante2 if conversacion.participante1 == request.user else conversacion.participante1
    
    # Obtener mensajes de la conversación
    mensajes = conversacion.mensajes.order_by('timestamp')
    
    # Marcar mensajes como leídos
    mensajes.filter(remitente=otro_usuario, leido=False).update(leido=True)
    
    return render(request, 'chat/chat_individual.html', {
        'conversacion': conversacion,
        'otro_usuario': otro_usuario,
        'mensajes': mensajes
    })

@login_required
def iniciar_chat(request, usuario_id):
    """Vista para iniciar una nueva conversación"""
    otro_usuario = get_object_or_404(User, id=usuario_id)
    
    if otro_usuario == request.user:
        return redirect('chat:lista_conversaciones')
    
    # Obtener o crear la conversación
    conversacion, created = Conversacion.objects.get_or_create(
        participante1=request.user if request.user.id < otro_usuario.id else otro_usuario,
        participante2=otro_usuario if request.user.id < otro_usuario.id else request.user
    )
    
    return redirect('chat:chat_individual', conversacion_id=conversacion.id)

@login_required
def api_mensajes(request, conversacion_id):
    """API para obtener mensajes de una conversación"""
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    
    # Verificar que el usuario es participante
    if request.user not in [conversacion.participante1, conversacion.participante2]:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    mensajes = conversacion.mensajes.order_by('timestamp')
    mensajes_data = []
    
    for mensaje in mensajes:
        mensajes_data.append({
            'id': mensaje.id,
            'texto': mensaje.texto,
            'remitente_id': mensaje.remitente.id,
            'remitente_nombre': mensaje.remitente.get_full_name() or mensaje.remitente.username,
            'timestamp': mensaje.timestamp.isoformat(),
            'leido': mensaje.leido,
            'es_mio': mensaje.remitente == request.user
        })
    
    return JsonResponse({'mensajes': mensajes_data})

@login_required
@csrf_exempt
@require_POST
def enviar_mensaje(request, conversacion_id):
    """API para enviar un mensaje (sin WebSocket)"""
    try:
        data = json.loads(request.body)
        texto = data.get('mensaje', '').strip()
        
        if not texto:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
        
        conversacion = get_object_or_404(Conversacion, id=conversacion_id)
        
        # Verificar que el usuario es participante
        if request.user not in [conversacion.participante1, conversacion.participante2]:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        # Crear el mensaje
        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            remitente=request.user,
            texto=texto
        )
        
        return JsonResponse({
            'success': True,
            'mensaje_id': mensaje.id,
            'timestamp': mensaje.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def buscar_usuarios(request):
    """Vista para buscar usuarios para iniciar chat"""
    query = request.GET.get('q', '')
    usuarios = []
    
    if query:
        usuarios = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)[:10]
    
    return render(request, 'chat/buscar_usuarios.html', {
        'usuarios': usuarios,
        'query': query
    })
