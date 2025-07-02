// Notificaciones
function actualizarBadgeNotificaciones(nuevoValor) {
  const countSpan = document.getElementById('notificacionesCount');
  const bell = document.getElementById('notificacionesBell');
  const valorAnterior = parseInt(countSpan.textContent) || 0;
  if (nuevoValor > 0) {
    countSpan.textContent = nuevoValor;
    countSpan.classList.remove('d-none');
    if (nuevoValor > valorAnterior) {
      countSpan.classList.add('bounce');
      bell.classList.add('bounce');
      setTimeout(() => {
        countSpan.classList.remove('bounce');
        bell.classList.remove('bounce');
      }, 700);
    }
  } else {
    countSpan.classList.add('d-none');
    countSpan.textContent = 0;
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

// Llamar al cargar y cada 30 segundos
setInterval(fetchMensajesNoLeidos, 30000);
document.addEventListener('DOMContentLoaded', fetchMensajesNoLeidos);

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