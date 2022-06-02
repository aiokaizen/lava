import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from lava.utils import get_log_filepath


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