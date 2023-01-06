# README #

This README would normally document whatever steps are necessary to get your application up and running.

## Description ##

This application is the base for all our django projects. It contains the core functionality that is required for any project (eg: Authentication, Logging, User management, Goup management, Authorization, Forgot password, Confirmation, ...etc).


## Set up ##

### 1. Configuration ###
  * Add the following settings to your project's settings.py:
```python


  # Default email settings
  ADMINS = [("Mouad Kommir", "k.mouad@ekblocks.com")]
  EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

  EMAIL_FILE_PATH = "/media/emails"  # The directory used by the file email backend to store output files.
  EMAIL_HOST = "smtp.gmail.com"
  EMAIL_HOST_USER = "noreply@infinityposhclub.com"
  EMAIL_HOST_PASSWORD = "imsdexwmxftilptr"
  EMAIL_PORT = 465
  EMAIL_SUBJECT_PREFIX = "[INFINITY POSH CLUB] "
  EMAIL_USE_TLS = False  # Whether to use a TLS (secure) connection when talking to the SMTP server. This is used for explicit TLS connections, generally on port 587. If you are experiencing hanging connections, see the implicit TLS setting EMAIL_USE_SSL.
  # Note that EMAIL_USE_TLS/EMAIL_USE_SSL are mutually exclusive, so only set one of those settings to True.
  EMAIL_USE_SSL = True  # Whether to use an implicit TLS (secure) connection when talking to the SMTP server. In most email documentation this type of TLS connection is referred to as SSL. It is generally used on port 465. If you are experiencing problems, see the explicit TLS setting EMAIL_USE_TLS.
  EMAIL_TIMEOUT = None  # Specifies a timeout in seconds for blocking operations like the connection attempt.
  EMAIL_USE_LOCALTIME = False  # Whether to send the SMTP Date header of email messages in the local time zone (True) or in UTC (False).

  AUTHENTICATION_BACKENDS = ['lava.backends.EmailOrUsernameAuthenticationBackend']
  
  MESSAGE_TAGS = {
      messages.DEBUG: "debug",
      messages.INFO: "info",
      messages.SUCCESS: "success",
      messages.WARNING: "warning",
      messages.ERROR: "danger",
  }

  STATIC_URL = "/static/"
  STATIC_ROOT = os.path.join(BASE_DIR, "static")
  # NB: This setting was commented to support the wkhtmltopdf library raising
  # an error when using the static tag. If we found a fix for that problem
  # we should uncomment this setting.
  # STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

  MEDIA_URL = "/media/"
  MEDIA_ROOT = os.path.join(BASE_DIR, "media")
  LOG_ROOT = os.path.join(BASE_DIR, "log")
  TMP_ROOT = os.path.join(BASE_DIR, "tmp")
  EXPOSED_URL = "/exposed/"
  EXPOSED_ROOT = os.path.join(BASE_DIR, "exposed")
  DEBUG_LEVEL = logging.DEBUG

  LOGO_FILE_PATH = "main/images/logo/logo.png"

  # DRF Settings
  REST_FRAMEWORK = {
      # Use Django's standard `django.contrib.auth` permissions,
      # or allow read-only access for unauthenticated users.
      "DEFAULT_PERMISSION_CLASSES": [
          "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
      ],
      "DEFAULT_AUTHENTICATION_CLASSES": (
          "rest_framework.authentication.TokenAuthentication",
      ),
      "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
      "PAGE_SIZE": 10,
  }

  # Djoser settings
  DJOSER = {
      "PASSWORD_RESET_CONFIRM_URL": "ekadmin/users/password/reset/confirm/{uid}/{token}",
      "ACTIVATION_URL": "ekadmin/users/activate/{uid}/{token}",
      "SEND_ACTIVATION_EMAIL": True,  # affects account creation and changing email
      "SEND_CONFIRMATION_EMAIL": False,  # Sent after registration (without any activation process)
      "PASSWORD_CHANGED_EMAIL_CONFIRMATION": False,  # Send email after password is changed successfully.
      # 'USER_CREATE_PASSWORD_RETYPE': True,  # must send re_password to create a user
      "SET_PASSWORD_RETYPE": True,  # must send re_new_password to change a user password
      "PASSWORD_RESET_CONFIRM_RETYPE": True,  # must send re_new_password to reset password
      "LOGOUT_ON_PASSWORD_CHANGE": True,
      "SERIALIZERS": {
          # Defaults---
          # 'user_create': 'djoser.serializers.UserCreateSerializer',
          # 'user_create_password_retype': 'djoser.serializers.UserCreatePasswordRetypeSerializer',
          # 'user_delete': 'djoser.serializers.UserDeleteSerializer',
          # 'activation': 'djoser.serializers.ActivationSerializer',
          # 'password_reset': 'djoser.serializers.SendEmailResetSerializer',
          # 'password_reset_confirm': 'djoser.serializers.PasswordResetConfirmSerializer',
          # 'password_reset_confirm_retype': 'djoser.serializers.PasswordResetConfirmRetypeSerializer',
          # 'set_password': 'djoser.serializers.SetPasswordSerializer',
          # 'set_password_retype': 'djoser.serializers.SetPasswordRetypeSerializer',
          # 'set_username': 'djoser.serializers.SetUsernameSerializer',
          # 'set_username_retype': 'djoser.serializers.SetUsernameRetypeSerializer',
          # 'username_reset': 'djoser.serializers.SendEmailResetSerializer',
          # 'username_reset_confirm': 'djoser.serializers.UsernameResetConfirmSerializer',
          # 'username_reset_confirm_retype': 'djoser.serializers.UsernameResetConfirmRetypeSerializer',
          # 'user_create': 'djoser.serializers.UserCreateSerializer',
          # 'user_create_password_retype': 'djoser.serializers.UserCreatePasswordRetypeSerializer',
          # 'user_delete': 'djoser.serializers.UserDeleteSerializer',
          # 'user': 'djoser.serializers.UserSerializer',
          # 'current_user': 'djoser.serializers.UserSerializer',
          # 'token': 'djoser.serializers.TokenSerializer',
          # 'token_create': 'djoser.serializers.TokenCreateSerializer',
          # Changed
          # 'user_create_password_retype': '',
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
          # 'activation': ['rest_framework.permissions.AllowAny'],
          # 'password_reset': ['rest_framework.permissions.AllowAny'],
          # 'password_reset_confirm': ['rest_framework.permissions.AllowAny'],
          # 'set_password': ['rest_framework.permissions.CurrentUserOrAdmin'],
          # 'username_reset': ['rest_framework.permissions.AllowAny'],
          # 'username_reset_confirm': ['rest_framework.permissions.AllowAny'],
          # 'set_username': ['rest_framework.permissions.CurrentUserOrAdmin'],
          # 'user_create': ['rest_framework.permissions.AllowAny'],
          # 'user_delete': ['rest_framework.permissions.CurrentUserOrAdmin'],
          # 'user': ['rest_framework.permissions.CurrentUserOrAdmin'],
          # 'user_list': ['rest_framework.permissions.CurrentUserOrAdmin'],
          # 'token_create': ['rest_framework.permissions.AllowAny'],
          # 'token_destroy': ['rest_framework.permissions.IsAuthenticated'],
      },
  }


  DATE_INPUT_FORMATS = [
      "%Y-%m-%d",
      "%d-%m-%Y",
      "%m/%d/%Y",  # '2006-10-25', '25-10-2006', '10/25/2006'
      "%b %d %Y",
      "%b %d, %Y",  # 'Oct 25 2006', 'Oct 25, 2006'
      "%d %b %Y",
      "%d %b, %Y",  # '25 Oct 2006', '25 Oct, 2006'
      "%B %d %Y",
      "%B %d, %Y",  # 'October 25 2006', 'October 25, 2006'
      "%d %B %Y",
      "%d %B, %Y",  # '25 October 2006', '25 October, 2006'
  ]

  DATETIME_INPUT_FORMATS = [
      "%m/%d/%Y %H:%M",  # '10/25/2006 14:30'
      "%m/%d/%Y %H:%M:%S",  # '10/25/2006 14:30:59'
      "%m/%d/%Y %H:%M:%S.%f",  # '10/25/2006 14:30:59.000200'
      "%d-%m-%Y %H:%M",  # '25-10-2006 14:30'
      "%d-%m-%Y %H:%M:%S",  # '25-10-2006 14:30:59'
      "%d-%m-%Y %H:%M:%S.%f",  # '25-10-2006 14:30:59.000200'
      "%Y-%m-%d %H:%M",  # '2006-10-25 14:30'
      "%Y-%m-%d %H:%M:%S",  # '2006-10-25 14:30:59'
      "%Y-%m-%d %H:%M:%S.%f",  # '2006-10-25 14:30:59.000200'
  ]

  GROUPS_ASSOCIATED_MODELS = {
      "CONTROLLERS": "main.Controller",
      "ORGANIZERS": "main.Organizer",
      "PARTICIPANTS": "main.Participant",
  }
  ALLOWED_SIGNUP_GROUPS = (
      ("organizers", _("Organizers")),
      ("participants", _("Participants")),
      ("controllers", _("Controllers")),
  )
  ALLOW_EMAIL_AUTHENTICATION = True
  ALLOW_USERNAME_AUTHENTICATION = True
  DENY_DUPLICATE_EMAILS = True
  EMAIL_GROUP_UNIQUE_TOGETHER = False

  AVAILABLE_NOTIFICATION_SETTINGS = [
      "allow_notifications_from_organiziers",
      "allow_notifications_from_subscribed_events",
      "allow_notifications_from_event_with_owned_tickets",
  ]


```
### 2. Dependencies ###
```shell
    pip install django==3.2
```
### Tests ###
### Deployment ###

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###
[EKBlocks](https://www.ekblocks.com)
