import qrcode

from django.core.validators import (
    EmailValidator, URLValidator, RegexValidator, BaseValidator
)
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from django.conf import settings

from lava import settings as lava_settings


def validate_empty_field(value):
    validator = RegexValidator('.+', _("This field is required"), "required")
    return validator(value)


def validate_email(email, groups, email_group_unique_together=None):

    from lava.models import User

    base_validator = EmailValidator()
    base_validator(email)

    # Override default behaviour
    if email_group_unique_together is None:
        email_group_unique_together = lava_settings.EMAIL_GROUP_UNIQUE_TOGETHER

    if not lava_settings.DENY_DUPLICATE_EMAILS:
        if groups and email_group_unique_together:
            try:
                User.objects.get(email=email, groups__in=groups)
                raise ValidationError(_("A user with that email already exists."))
            except User.DoesNotExist:
                pass
        return email

    try:
        User.objects.get(email=email)
        raise ValidationError(_("A user with that email already exists."))
    except User.DoesNotExist:
        return email


class SchemelessURLValidator(URLValidator):
    def __call__(self, value):
        if len(value.split("://")) == 1:
            if value[0] != "/":
                raise ValidationError(
                    _("A local url must start with a forward slash `/`")
                )
            value = "https://www.ekblocks.com" + value
        super().__call__(value)


@deconstructible
class ExactLengthValidator(BaseValidator):
    message = ngettext_lazy(
        'Ensure this value has exactly %(limit_value)d character (it has %(show_value)d)',
        'Ensure this value has exactly %(limit_value)d characters (it has %(show_value)d)',
        'limit_value')
    code = 'exact_length'

    def compare(self, a, b):
        return a != b

    def clean(self, x):
        return len(x)


def qr_code_validator(value):
    try:
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(value)
        qr.make(fit=True)
    except:
        raise ValidationError(_('Invalid QR code'))


def validate_notifications_settings(value):
    """Raises a ValidationError if the value is not valid, otherwize, returns None."""

    custom_notification_settings = getattr(settings, "AVAILABLE_NOTIFICATION_SETTINGS", [])
    available_settings = [
        "allow_push_notifications",
        "allow_email_notifications",
        *custom_notification_settings
    ]

    if type(value) != dict:
        raise ValidationError(_("The notifications settings must be a dictionary."))

    for k, v in value.items():
        if k not in available_settings:
            raise ValidationError(
                _(
                    "`%(key)s` is not a valid key for notifications settings."
                    % {"key": k}
                )
            )
        if type(v) != bool:
            raise ValidationError(
                _("The value of `%(key)s` is not a valid boolean value." % {"key": k})
            )
