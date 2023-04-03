import os

from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librarian.settings.settings_asgi')

from channels.routing import ProtocolTypeRouter, URLRouter

from lava.ws.consumers import ChatConsumer, NotificationConsumer
from lava.middleware import SocketTokenAuthMiddlewareStack


websocket_urlpatterns = [
    path('ws/chat/', ChatConsumer.as_asgi()),
    path('ws/chat/<int:conversation_id>/', ChatConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    'websocket': SocketTokenAuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            ),
        )
})
