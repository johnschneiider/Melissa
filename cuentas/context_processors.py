def user_context(request):
    """
    Procesador de contexto personalizado para agregar información del usuario
    a todas las plantillas
    """
    context = {}
    
    if request.user.is_authenticated:
        context['es_cliente'] = getattr(request.user, 'tipo', None) == 'cliente'
        context['es_negocio'] = getattr(request.user, 'tipo', None) == 'negocio'
        context['tiene_negocios'] = hasattr(request.user, 'negocios') and request.user.negocios.exists()
        context['nombre_usuario'] = request.user.get_full_name() or request.user.username
    else:
        context['es_cliente'] = False
        context['es_negocio'] = False
        context['tiene_negocios'] = False
        context['nombre_usuario'] = None
    
    return context

def user_type(request):
    """
    Context processor para hacer disponible el tipo de usuario en todas las plantillas
    """
    context = {
        'is_cliente': False,
        'is_negocio': False,
    }
    
    if request.user.is_authenticated:
        context['is_cliente'] = request.user.tipo == 'cliente'
        context['is_negocio'] = request.user.tipo == 'negocio'
    
    return context 