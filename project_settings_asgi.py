from lava.project_settings import *


INSTALLED_APPS = [
    "daphne",
    *INSTALLED_APPS,
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': "channels.layers.InMemoryChannelLayer"
    },
}
