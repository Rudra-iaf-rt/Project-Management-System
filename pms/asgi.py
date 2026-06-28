# pms/asgi.py - PRODUCTION READY
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms.settings')
django.setup()

from apps.chat.routing import websocket_urlpatterns as chat_urlpatterns
from apps.meetings.routing import websocket_urlpatterns as meeting_urlpatterns

combined_urlpatterns = chat_urlpatterns + meeting_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(combined_urlpatterns)
    ),
})