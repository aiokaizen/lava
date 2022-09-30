import logging
import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from lava.utils import get_log_filepath, init_firebase


logging.basicConfig(
    filename=get_log_filepath(), level=settings.DEBUG_LEVEL
)


GENDER_CHOICES = (
    ("", _("")),
    ("F", _("Female")),
    ("M", _("Male"))
)

NOTIFICATION_CATEGORY_CHOICES = (
    ("alert", _("Alert")),
)

ALLOWED_SIGNUP_GROUPS = getattr(settings, 'ALLOWED_SIGNUP_GROUPS', (
    # (groupe1_id, _("Group name")),
    # (groupe2_id, _("Group name")),
    # (groupe3_id, _("Group name")),
))

# This setting is used to map groups to other models.
# When creating a user in a certain group, an object
# from the group's mapped model is created and associated to the user.
GROUPS_ASSOCIATED_MODELS = getattr(settings, "GROUPS_ASSOCIATED_MODELS", {
#   "ADMINS": "ecom.models.Admin",
#   "CONTENT_MANAGERS": "myapp.ContentManager",
#   "CONTENT_CREATERS": "myapp.ContentCreater",
})

DENY_DUPLICATE_EMAILS = getattr(settings, 'DENY_DUPLICATE_EMAILS', False)
EMAIL_GROUP_UNIQUE_TOGETHER = getattr(
    # If `DENY_DUPLICATE_EMAILS` is set to True, it overrides this setting.
    settings, 'EMAIL_GROUP_UNIQUE_TOGETHER', False
)

BREADCRUMBS_DEPTH_LEVEL = getattr(settings, 'BREADCRUMBS_DEPTH_LEVEL', 3)

LOGO_FILE_PATH = getattr(settings, "LOGO_FILE_PATH", 'lava/assets/images/email/logo.png')

FIREBASE_CREDENTIALS_FILE_PATH = os.path.join(settings.BASE_DIR, 'firebase-adminsdk-private-key.json')
FIREBASE_ACTIVATED = False

_init_firebase_result = init_firebase()
if _init_firebase_result.success:
    FIREBASE_ACTIVATED = True
