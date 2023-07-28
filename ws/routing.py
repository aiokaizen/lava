import os

from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librarian.settings.settings_asgi')
asgi_application = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from lava.ws.consumers import ChatConsumer, NotificationConsumer, BackUpConsumer
from lava.middleware import SocketTokenAuthMiddlewareStack


websocket_urlpatterns = [
    path('ws/chat/', ChatConsumer.as_asgi()),
    path('ws/chat/<int:conversation_id>/', ChatConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    path('ws/backup/status/', BackUpConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": asgi_application,
    'websocket': AllowedHostsOriginValidator(
            SocketTokenAuthMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns
                ),
            )
        )
})
