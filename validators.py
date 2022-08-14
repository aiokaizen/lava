from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from lava import settings as lava_settings
from lava.models import User


def validate_email(email, groups):
    
    base_validator = EmailValidator()
    base_validator(email)
    
    if not lava_settings.DENY_DUPLICATE_EMAILS:
        if groups and lava_settings.EMAIL_GROUP_UNIQUE_TOGETHER:
            try:
                User.objects.get(email=email, groups__in=groups)
                raise ValidationError(
                    _("A user with that email already exists.")
                )
            except User.DoesNotExist:
                pass
        return email

    try:
        User.objects.get(email=email)
        raise ValidationError(_("A user with that email already exists."))
    except User.DoesNotExist:
        return email
