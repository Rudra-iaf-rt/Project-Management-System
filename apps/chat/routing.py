# apps/chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat WebSocket: expects a team ID in the URL
    re_path(r'ws/chat/(?P<team_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]