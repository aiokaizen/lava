import os
import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


PROJECT_NAME = slugify(os.path.basename(os.path.normpath(settings.BASE_DIR))).replace('-', '_')


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9@xy8cgd$v6-zrbbsgk!krmp^9-syglu^z&4p-n^@2fs1_cj#^'
try:
    with open(f'/etc/secrets/{PROJECT_NAME}_secret.key') as f:
        SECRET_KEY = f.read().strip()
    logging.info("SECRET_KEY file loaded successfully.")
except FileNotFoundError:
    logging.warning("SECRET_KEY file not found, using a default value.")


DEBUG_LEVEL = logging.DEBUG


AUTH_USER_MODEL = 'lava.User'
LOGIN_URL = '/ekadmin/login/'
AUTHENTICATION_BACKENDS = [
    'lava.backends.EmailOrUsernameAuthenticationBackend'
]


ALLOWED_HOSTS = []


INSTALLED_APPS_PREFIX = [
    "admin_interface",
    "colorfield",

    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

INSTALLED_APPS_SUFFIX = [
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "djoser",
    "drf_spectacular",
    'easy_thumbnails',

    'lava',
]

INSTALLED_APPS = [
    *INSTALLED_APPS_PREFIX,
    *settings.INSTALLED_APPS,
    *INSTALLED_APPS_SUFFIX
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'lava.middleware.MaintenanceModeMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    # "https://example.com",
    # "https://sub.example.com",
    # "http://localhost:8080",
    # "http://127.0.0.1:9000",
]
CORS_ALLOW_ALL_ORIGINS = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(settings.BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# DRF Settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
    "EXCEPTION_HANDLER": "lava.exceptions.lava_drf_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    # Desable Browsable API
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer']
}


# Djoser settings
DJOSER = {
    "PASSWORD_RESET_CONFIRM_URL": "ekadmin/users/password/reset/confirm/{uid}/{token}",
    "ACTIVATION_URL": "ekadmin/users/activate/{uid}/{token}",
    "SEND_ACTIVATION_EMAIL": False,  # affects account creation and changing email
    "SEND_CONFIRMATION_EMAIL": False,  # Sent after registration (without any activation process)
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": False,  # Send email after password is changed successfully.
    # 'USER_CREATE_PASSWORD_RETYPE': True,  # must send re_password to create a user
    "SET_PASSWORD_RETYPE": True,  # must send re_new_password to change a user password
    "PASSWORD_RESET_CONFIRM_RETYPE": True,  # must send re_new_password to reset password
    "LOGOUT_ON_PASSWORD_CHANGE": True,
    "SERIALIZERS": {
        "user": "lava.serializers.UserSerializer",
        "current_user": "lava.serializers.UserSerializer",
        "user_create": "lava.serializers.UserSerializer",
    },
    "EMAIL": {
        "activation": "lava.email.ActivationEmail",
        "confirmation": "lava.email.ConfirmationEmail",
        "password_reset": "lava.email.PasswordResetEmail",
        "password_changed_confirmation": "lava.email.PasswordChangedConfirmationEmail",
        "username_changed_confirmation": "lava.email.UsernameChangedConfirmationEmail",
        "username_reset": "lava.email.UsernameResetEmail",
    },
    "CONSTANTS": {
        "messages": "lava.constants.Messages",
    },
    "PERMISSIONS": {
    },
}

X_FRAME_OPTIONS = 'ALLOWALL'
XS_SHARING_ALLOWED_METHODS = ['POST','GET','OPTIONS', 'PUT', 'DELETE']


# Thumbnails settings
BASE_THUMBNAIL_ALIASES = {
    **getattr(settings, 'THUMBNAIL_ALIASES', {})
}
THUMBNAIL_ALIASES = {
    '': {
        'thumbnail': {'size': (50, 50), 'crop': 'smart'},
        'avatar': {'size': (150, 150), 'crop': 'smart'},
        **BASE_THUMBNAIL_ALIASES.pop('', {})
    },
    'lava.User.cover_picture': {
        'cover': {'size': (1200, 250), 'crop': 'smart'},
    },
    **BASE_THUMBNAIL_ALIASES
}


# SPECTACULAR Docs Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Lava",
    'DESCRIPTION': 'General purpose management system',
    'VERSION': '3.0.2',
    'SERVE_INCLUDE_SCHEMA': False,
    "SWAGGER_UI_FAVICON_HREF": 'lava/assets/images/logo/favicon.png',
}


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'
LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
    ('fr', _('Frensh')),
]

TIME_ZONE = 'Africa/Casablanca'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(settings.BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'media')

LOG_ROOT = os.path.join(settings.BASE_DIR, 'log')

TMP_ROOT = os.path.join(settings.BASE_DIR, "tmp")

EXPOSED_URL = "/exposed/"
EXPOSED_ROOT = os.path.join(settings.BASE_DIR, "exposed")


FILE_PATTERNS = {
    '*.html': 'django',
    '*.txt': 'django',
    '*.js': 'javascript',
    '*.py': 'gettext',
}


# Maintenance mode
MAINTENANCE_MODE = int(os.environ.get(f"{PROJECT_NAME.upper()}_MAINTENANCE_MODE", 0))
MAINTENANCE_BYPASS_QUERY = os.environ.get(
    "MAINTENANCE_BYPASS_QUERY", "pwd=ekadmin_pass"
)


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'