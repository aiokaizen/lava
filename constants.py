import enum

from django.utils.translation import gettext_lazy as _


class DELETE_POLICY(enum.Enum):
    HARD_DELETE = 0
    SOFT_DELETE = 1


# These messages are used by Djoser
class Messages(object):
    INVALID_CREDENTIALS_ERROR = _("Unable to log in with provided credentials.")
    INACTIVE_ACCOUNT_ERROR = _("User account is disabled.")
    INVALID_TOKEN_ERROR = _("Invalid token for given user.")
    INVALID_UID_ERROR = _("Invalid user id or user doesn't exist.")
    STALE_TOKEN_ERROR = _("User is already activated.")
    PASSWORD_MISMATCH_ERROR = _("The two password fields didn't match.")
    USERNAME_MISMATCH_ERROR = _("The two {0} fields didn't match.")
    INVALID_PASSWORD_ERROR = _("Invalid password.")
    EMAIL_NOT_FOUND = _("User with given email does not exist.")
    CANNOT_CREATE_USER_ERROR = _("Unable to create an account.")
