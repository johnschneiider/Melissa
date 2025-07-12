// Notificaciones
function actualizarBadgeNotificaciones(nuevoValor) {
  const countSpan = document.getElementById('notificacionesCount');
  const bell = document.getElementById('notificacionesBell');
  
  // Debug: verificar si los elementos existen
  console.log('actualizarBadgeNotificaciones llamado con:', nuevoValor);
  console.log('countSpan existe:', !!countSpan);
  console.log('bell existe:', !!bell);
  
  if (!countSpan || !bell) {
    console.error('Elementos de notificaciones no encontrados');
    return;
  }
  
  const valorAnterior = parseInt(countSpan.textContent) || 0;
  console.log('Valor anterior:', valorAnterior, 'Nuevo valor:', nuevoValor);
  
  if (nuevoValor > 0) {
    countSpan.textContent = nuevoValor;
    // Usar Bootstrap d-none en lugar de display: flex
    countSpan.classList.remove('d-none');
    console.log('Badge actualizado:', countSpan.textContent, 'Clases:', countSpan.className);
    
    // Si hay nuevas notificaciones, mostrar animación
    if (nuevoValor > valorAnterior && valorAnterior > 0) {
      // Animación más llamativa para nuevas notificaciones
      countSpan.classList.add('bounce');
      bell.classList.add('shake');
      
      // Cambiar color temporalmente
      countSpan.style.background = 'var(--color-teal-accent)';
      countSpan.style.color = 'white';
      
      setTimeout(() => {
        countSpan.classList.remove('bounce');
        bell.classList.remove('shake');
        countSpan.style.background = '';
        countSpan.style.color = '';
      }, 1000);
    } else if (nuevoValor > valorAnterior) {
      // Primera notificación
      countSpan.classList.add('pulse');
      bell.classList.add('pulse');
      
      setTimeout(() => {
        countSpan.classList.remove('pulse');
        bell.classList.remove('pulse');
      }, 500);
    }
  } else {
    countSpan.classList.add('d-none');
    countSpan.textContent = 0;
    console.log('Badge ocultado');
  }
}

// Chat (preparado para el futuro)
function actualizarBadgeChat(nuevoValor) {
  const chatCount = document.getElementById('chatCount');
  const chatIcon = document.getElementById('chatIcon');
  const valorAnterior = parseInt(chatCount.textContent) || 0;
  if (nuevoValor > 0) {
    chatCount.textContent = nuevoValor;
    chatCount.classList.remove('d-none');
    if (nuevoValor > valorAnterior) {
      chatCount.classList.add('bounce');
      chatIcon.classList.add('bounce');
      setTimeout(() => {
        chatCount.classList.remove('bounce');
        chatIcon.classList.remove('bounce');
      }, 700);
    }
  } else {
    chatCount.classList.add('d-none');
    chatCount.textContent = 0;
  }
}

// Consulta periódica de mensajes no leídos
function fetchMensajesNoLeidos() {
  fetch('/chat/api/mensajes-no-leidos/')
    .then(resp => resp.json())
    .then(data => {
      if (typeof data.no_leidos !== 'undefined') {
        actualizarBadgeChat(data.no_leidos);
      }
    })
    .catch(() => {});
}

// Consulta periódica de notificaciones
function fetchNotificaciones() {
  console.log('Fetching notificaciones...');
  fetch('/cuentas/api/notificaciones/')
    .then(resp => resp.json())
    .then(data => {
      console.log('Respuesta de notificaciones:', data);
      if (typeof data.no_leidas !== 'undefined') {
        const valorAnterior = parseInt(document.getElementById('notificacionesCount')?.textContent) || 0;
        console.log('No leídas:', data.no_leidas, 'Valor anterior:', valorAnterior);
        actualizarBadgeNotificaciones(data.no_leidas);
        
        // Mostrar notificación push si hay nuevas notificaciones
        if (data.no_leidas > valorAnterior && data.no_leidas > 0) {
          mostrarNotificacionPush('Nueva notificación', 'Tienes una nueva notificación en Melissa');
        }
      }
    })
    .catch((error) => {
      console.error('Error fetching notificaciones:', error);
    });
}

// Función para mostrar notificación push del navegador
function mostrarNotificacionPush(titulo, mensaje) {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(titulo, {
      body: mensaje,
      icon: '/static/images/ui/melissa-pattern.png',
      badge: '/static/images/ui/melissa-pattern.png'
    });
  }
}

// Solicitar permisos de notificación al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
});

// Llamar al cargar y cada 10 segundos para actualizaciones más rápidas
setInterval(fetchMensajesNoLeidos, 10000);
setInterval(fetchNotificaciones, 10000);
document.addEventListener('DOMContentLoaded', function() {
  fetchMensajesNoLeidos();
  fetchNotificaciones();
  
  // Test inicial para verificar que el badge funciona
  setTimeout(() => {
    console.log('Test inicial del badge...');
    const countSpan = document.getElementById('notificacionesCount');
    if (countSpan) {
      console.log('Badge encontrado, probando visibilidad...');
      countSpan.textContent = '1';
      countSpan.classList.remove('d-none');
      console.log('Badge actualizado:', countSpan.textContent, 'Clases:', countSpan.className);
      
      // Ocultar después de 3 segundos
      setTimeout(() => {
        countSpan.classList.add('d-none');
        console.log('Badge ocultado');
      }, 3000);
    } else {
      console.error('Badge no encontrado en el DOM');
    }
  }, 2000);
});

// Hook para integración con AJAX existente
document.addEventListener('DOMContentLoaded', function() {
  // Hook para notificaciones
  if (window.cargarNotificaciones) {
    const originalCargar = window.cargarNotificaciones;
    window.cargarNotificaciones = async function() {
      const data = await originalCargar.apply(this, arguments);
      if (data && typeof data.no_leidas !== 'undefined') {
        actualizarBadgeNotificaciones(data.no_leidas);
      }
      return data;
    };
  }
}); 