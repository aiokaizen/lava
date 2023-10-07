from logging import critical
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from lava.models.models import Permission
from lava.settings import ALLOW_EMAIL_AUTHENTICATION, ALLOW_USERNAME_AUTHENTICATION


class BaseModelBackEnd(ModelBackend):
    def _get_group_permissions(self, user_obj):
        user_groups_field = get_user_model()._meta.get_field("groups")
        user_groups_query = "group__group__%s" % user_groups_field.related_query_name()
        return Permission.objects.filter(**{user_groups_query: user_obj})


class EmailOrUsernameAuthenticationBackend(BaseModelBackEnd):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            criteria = EmailOrUsernameAuthenticationBackend.get_search_criteria(
                username
            )
            user = UserModel.objects.get(criteria)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None

    @classmethod
    def get_authentication_methods(cls):
        allow_email_auth, allow_username_auth = False, False

        if ALLOW_USERNAME_AUTHENTICATION:
            allow_username_auth = True
        if ALLOW_EMAIL_AUTHENTICATION:
            allow_email_auth = True

        if not allow_email_auth and not allow_username_auth:
            allow_email_auth = True

        return allow_email_auth, allow_username_auth

    @classmethod
    def get_search_criteria(cls, username):
        (
            allow_email_auth,
            allow_username_auth,
        ) = EmailOrUsernameAuthenticationBackend.get_authentication_methods()
        criteria = Q()
        if allow_email_auth:
            criteria |= Q(email__iexact=username)
        if allow_username_auth:
            criteria |= Q(username__iexact=username)
        return criteria
