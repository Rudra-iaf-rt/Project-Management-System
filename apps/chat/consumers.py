# apps/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle new WebSocket connection"""
        self.team_id = self.scope['url_route']['kwargs']['team_id']
        self.room_group_name = f'chat_{self.team_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connected: Team {self.team_id}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected: Team {self.team_id}")

    async def receive(self, text_data):
        """Handle incoming WebSocket message"""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            username = self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonymous'

            # Save message to database (optional, can be commented out for now)
            await self.save_message(username, message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'timestamp': datetime.now().isoformat(),
                }
            )
        except Exception as e:
            print(f"Error receiving message: {e}")

    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, username, message):
        """Save message to database"""
        from apps.chat.models import ChatMessage
        from apps.accounts.models import User
        from apps.teams.models import Team
        
        try:
            user = User.objects.get(username=username)
            team = Team.objects.get(id=self.team_id)
            ChatMessage.objects.create(
                user=user,
                team=team,
                message=message
            )
        except Exception as e:
            print(f"Error saving message: {e}")