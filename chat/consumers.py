import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversacion, Mensaje

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Crear un grupo único para este usuario
        self.room_name = f"user_{self.user.id}"
        self.room_group_name = f"chat_{self.room_name}"
        
        # Unirse al grupo del chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar mensaje de conexión exitosa
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al chat'
        }))

    async def disconnect(self, close_code):
        # Salir del grupo del chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'mark_read':
            await self.handle_mark_read(text_data_json)

    async def handle_chat_message(self, data):
        destinatario_id = data.get('destinatario_id')
        mensaje_texto = data.get('message', '')
        
        if not destinatario_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'ID de destinatario requerido'
            }))
            return
        
        # Guardar el mensaje en la base de datos
        mensaje = await self.save_message(destinatario_id, mensaje_texto)
        
        if mensaje:
            # Enviar mensaje al destinatario
            await self.channel_layer.group_send(
                f"chat_user_{destinatario_id}",
                {
                    'type': 'chat_message',
                    'message': mensaje_texto,
                    'remitente_id': self.user.id,
                    'remitente_nombre': self.user.get_full_name() or self.user.username,
                    'timestamp': mensaje.timestamp.isoformat(),
                    'mensaje_id': mensaje.id
                }
            )
            
            # Confirmar envío al remitente
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message': mensaje_texto,
                'destinatario_id': destinatario_id,
                'timestamp': mensaje.timestamp.isoformat(),
                'mensaje_id': mensaje.id
            }))

    async def handle_mark_read(self, data):
        mensaje_id = data.get('mensaje_id')
        if mensaje_id:
            await self.mark_message_as_read(mensaje_id)

    async def chat_message(self, event):
        # Enviar mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'remitente_id': event['remitente_id'],
            'remitente_nombre': event['remitente_nombre'],
            'timestamp': event['timestamp'],
            'mensaje_id': event['mensaje_id']
        }))

    @database_sync_to_async
    def save_message(self, destinatario_id, mensaje_texto):
        try:
            destinatario = User.objects.get(id=destinatario_id)
            
            # Obtener o crear la conversación
            conversacion, created = Conversacion.objects.get_or_create(
                participante1=self.user if self.user.id < destinatario.id else destinatario,
                participante2=destinatario if self.user.id < destinatario.id else self.user
            )
            
            # Crear el mensaje
            mensaje = Mensaje.objects.create(
                conversacion=conversacion,
                remitente=self.user,
                texto=mensaje_texto
            )
            
            return mensaje
        except User.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error al guardar mensaje: {e}")
            return None

    @database_sync_to_async
    def mark_message_as_read(self, mensaje_id):
        try:
            mensaje = Mensaje.objects.get(id=mensaje_id, leido=False)
            mensaje.leido = True
            mensaje.save()
            return True
        except Mensaje.DoesNotExist:
            return False 