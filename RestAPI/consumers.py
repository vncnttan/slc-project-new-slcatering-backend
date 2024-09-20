import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

class QRCodeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        print(f"!!! Connecting : {self.scope['url_route']}")
        self.group_name = f'user_{self.user_id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        return self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def payment_success(self, event):
        print(f"Payment Success Triggered")
        await self.send(text_data=json.dumps({
            'type': 'payment_success',
            'message': event['message']
        }))