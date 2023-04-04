from lava.project_settings import *


INSTALLED_APPS = [
    "daphne",
    *INSTALLED_APPS,
]

# Channels settings
ASGI_APPLICATION = "lava.ws.routing.application"
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': "channels.layers.InMemoryChannelLayer"
    },
    'notification': {
        'BACKEND': "channels.layers.InMemoryChannelLayer"
    },
    'backup': {
        'BACKEND': "channels.layers.InMemoryChannelLayer"
    }
}
