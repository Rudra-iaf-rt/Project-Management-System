# pms/asgi.py - PRODUCTION READY
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms.settings')
django.setup()
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.chat.routing import websocket_urlpatterns as chat_urlpatterns
from apps.meetings.routing import websocket_urlpatterns as meeting_urlpatterns

combined_urlpatterns = chat_urlpatterns + meeting_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(combined_urlpatterns)
    ),
})