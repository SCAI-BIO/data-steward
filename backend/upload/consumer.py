
from channels.generic.websocket import WebsocketConsumer
import json
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json

class ProccessConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pid']
        self.room_group_name = 'process_%s' % self.room_name
        #print(self.room_group_name)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        
        cache.set('websocket_connection', 'connected', 30)
        #print(cache.get('websocket_connection'))
        

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        cache.delete('websocket_connection')

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        #print("test2")
        if message == 'cancel':
            cache.set('cancel','true', 60)
            return
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'status_message',
                'message': message
            }
        )

    # Receive message from room group
    def status_message(self, event):
        #print("test")
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'status': 'True',
            'message': message
        }))
    def error_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message,
            'error': 'True'
        }))
    def success_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message,
            'success': 'True'
        }))
    def update_message(self, event):
        proc = event['proc']
        self.send(text_data=json.dumps({
            'proc': proc,
            'update': 'True'
        }))

