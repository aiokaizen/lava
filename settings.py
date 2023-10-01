from datetime import datetime
import logging
import os

try:
    import firebase_admin
    from firebase_admin import credentials
except ImportError:
    firebase_admin = None

from django.conf import settings
from django.utils.translation import gettext_lazy as _


LOG_ROOT = getattr(settings, "LOG_ROOT ", os.path.join(settings.BASE_DIR, "log"))

FIREBASE_CREDENTIALS_FILE_PATH = os.path.join(
    settings.BASE_DIR, "firebase-adminsdk-private-key.json"
)


def init_firebase():
    creds_file_path = FIREBASE_CREDENTIALS_FILE_PATH
    if firebase_admin is None:
        return (False, _("Firebase is not installed"))

    if not os.path.exists(creds_file_path):
        logging.info("Firebase credentials file does not exist.")
        return (False, _("Firebase credentials file does not exist."))

    try:
        creds = credentials.Certificate(creds_file_path)
        # cred = credentials.RefreshToken(creds_file_path)
        default_app = firebase_admin.initialize_app(creds)
        return (True, "")
    except Exception as e:
        logging.error(e)
        return (False, str(e))


def get_log_filepath():
    now = datetime.now()
    current_hour = now.strftime("%Y%m%d_%H")
    filename = f"{current_hour}.log"
    filepath = os.path.join(LOG_ROOT, filename)
    if not os.path.exists(LOG_ROOT):
        os.makedirs(LOG_ROOT)
    return filepath


logging.basicConfig(filename=get_log_filepath(), level=settings.DEBUG_LEVEL)


GENDER_CHOICES = (("", ""), ("F", _("Female")), ("M", _("Male")))

NOTIFICATION_CATEGORY_CHOICES = (("alert", _("Alert")),)

ALLOWED_SIGNUP_GROUPS = getattr(
    settings,
    "ALLOWED_SIGNUP_GROUPS",
    (
        # (groupe1_id, _("Group name")),
        # (groupe2_id, _("Group name")),
        # (groupe3_id, _("Group name")),
    ),
)

HOST = getattr(settings, "HOST", "localhost:8000")

EKBLOCKS_COLOR = "#1cab98"

ALLOW_EMAIL_AUTHENTICATION = getattr(settings, "ALLOW_EMAIL_AUTHENTICATION", True)
ALLOW_USERNAME_AUTHENTICATION = getattr(settings, "ALLOW_USERNAME_AUTHENTICATION", True)
DENY_DUPLICATE_EMAILS = getattr(settings, "DENY_DUPLICATE_EMAILS", True)
EMAIL_GROUP_UNIQUE_TOGETHER = getattr(
    # If `DENY_DUPLICATE_EMAILS` is set to True, it overrides this setting.
    settings,
    "EMAIL_GROUP_UNIQUE_TOGETHER",
    False,
)

RESULT_TYPE_CHOICES = (
    ("success", _("Success")),
    ("warning", _("Warning")),
    ("error", _("Error")),
)

ACTIVATE_PAYEMENTS = getattr(settings, "ACTIVATE_PAYEMENTS", True)

BACKUP_TYPE_CHOICES = (
    ("full_backup", _("Full backup")),
    ("db_backup", _("Database backup")),
)

BACKUP_STATUS_CHOICES = (
    ("running", _("Running")),
    ("completed", _("Completed")),
    ("failed", _("Failed")),
)

BACKUP_LOCK_TAG_PATH = os.path.join(settings.BASE_DIR, ".back_up_in_progress")

_INNER_REPOSITORIES = getattr(settings, "INNER_REPOSITORIES", [])
INNER_REPOSITORIES = [*_INNER_REPOSITORIES, "lava"]

BREADCRUMBS_DEPTH_LEVEL = getattr(settings, "BREADCRUMBS_DEPTH_LEVEL", 3)

LOGO_FILE_PATH = getattr(settings, "LOGO_FILE_PATH", "lava/assets/images/logo/logo.png")

FIREBASE_ACTIVATED = init_firebase()[0]

REMOTE_BACKUP_CONF = getattr(
    settings,
    "REMOTE_BACKUP_CONF",
    {
        "server_name": "backup_server",  # IP address or domain name
        "login_user": "ekadmin",
        "backup_folder": "/var/backup/lava",
    },
)
TMP_ROOT = getattr(settings, "TMP_ROOT", os.path.join(settings.BASE_DIR, "tmp"))


BACKUP_COMPLETED_NOTIFICATION_ID = "backup_completed_alert"
_NOTIFICATION_GROUPS_NAMES = {
    "user_added_alert": {
        "name": _("User creation alert"),
        "description": _("This notification is sent when a new user is created."),
    },
    "user_deleted_alert": {
        "name": _("User deletion alert"),
        "description": _("This notification is sent when a user is deleted."),
    },
    "group_added_alert": {
        "name": _("Group creation alert"),
        "description": _("This notification is sent when a new group is created."),
    },
    "group_deleted_alert": {
        "name": _("Group deletion alert"),
        "description": _("This notification is sent when a group is deleted."),
    },
    "permission_changed_alert": {
        "name": _("Permission update alert"),
        "description": _(
            "This notification is sent when a permission has been affected or revoked from a user or group."
        ),
    },
    BACKUP_COMPLETED_NOTIFICATION_ID: {
        "name": _("Backup completed alert"),
        "description": _("This notification is sent when a backup is completed."),
    },
}
NOTIFICATION_GROUPS_NAMES = {
    **_NOTIFICATION_GROUPS_NAMES,
    **getattr(settings, "NOTIFICATION_GROUPS_NAMES", {}),
}


CLASS_NAME_CHOICES = (
    ("users", _("Users")),
    ("groups", _("Groups")),
    ("permissions", _("Permissions")),
    *getattr(settings, "CHOICES_API_CLASS_NAME_CHOICES", []),
)

CLASS_NAME_CHOICES_MAPPING = {
    "users": "lava.User",
    "groups": "lava.Group",
    "permissions": "lava.Permission",
    **getattr(settings, "CHOICES_API_CLASS_NAME_CHOICES_MAPPING", {}),
}

HIDE_ADMINS_GROUP = getattr(settings, "HIDE_ADMINS_GROUP", False)
HIDE_PERMISSIONS_FIELDS_FROM_ADMIN = getattr(
    settings, "HIDE_PERMISSIONS_FIELDS_FROM_ADMIN", False
)

LOCKED_PERMISSIONS = getattr(settings, "LOCKED_PERMISSIONS", {
    "models": [
        # "app_name.model_name"

        # e.g.
        # "lava.user",
        # "lava.notificationgroup"
    ],
    "permissions": [
        # "app_name.permission_codename"

        # e.g.
        # "lava.add_user",
        # "lava.soft_delete_user",
    ],
})


# Chat models settings
TIMEUNIT_CHOICES = ["days", "hours", "minutes"]

CHAT_MESSAGE_CHOICES = (
    ("text", _("Text")),
    ("image", _("Image")),
)
