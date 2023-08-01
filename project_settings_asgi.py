from lava.project_settings import *


INSTALLED_APPS = [
    "daphne",
    *INSTALLED_APPS,
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': "channels_redis.core.RedisChannelLayer",
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
