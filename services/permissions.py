from typing import Union

from rest_framework.permissions import IsAuthenticated

from lava.enums import PermissionActionName
from lava.utils.utils import camelcase_to_snakecase


# Generic Model PERMISSIONS
def has_permission(user, model, action: Union[PermissionActionName, str]):
    """
    Checks if a user has the permission to perform the action on the specified model.
    If action type is 'str' the model param is not used.
    """
    app_label = model._meta.app_label
    permission_name = action

    if not isinstance(action, str):
        model_name = camelcase_to_snakecase(model.__name__)
        permission_name = f"{action.value}_{model_name}"

    has_perm = user.has_perm(f"{app_label}.{permission_name}")
    return has_perm


def get_model_permission_class(model, action: Union[PermissionActionName, str]):
    """
    Returns a PermissionClass that checks if a user has the permission to perform
    the action on the specified model.
    """

    class PermissionClass(IsAuthenticated):

        def has_permission(self, request, view):
            is_authenticated = super().has_permission(request, view)
            user = request.user
            return is_authenticated and has_permission(user, model, action)

    return PermissionClass


# Notification permissions
def can_send_notifications(user):
    has_perm = user.has_perm('lava.send_notifications')
    return has_perm


# User Profile permissions
def can_change_current_user(user):
    has_perm = user.has_perm('lava.change_current_user')
    return has_perm


def can_delete_current_user(user):
    has_perm = user.has_perm('lava.delete_current_user')
    return has_perm


def can_soft_delete_current_user(user):
    has_perm = user.has_perm('lava.soft_delete_current_user')
    return has_perm


def can_set_permission(user):
    has_perm = user.has_perm('lava.set_permission')
    return has_perm


def can_export_permission(user):
    has_perm = user.has_perm('lava.export_permission')
    return has_perm


# ActivityJournal permissions
def can_list_logentry(user):
    has_perm = user.has_perm('lava.list_logentry')
    return has_perm


def can_export_logentry(user):
    has_perm = user.has_perm('lava.export_logentry')
    return has_perm
