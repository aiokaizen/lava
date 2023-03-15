from rest_framework.permissions import IsAuthenticated

from lava.services.permissions import *


# General permissions
class IsSuperUser(IsAuthenticated):
    """
    Checks if a user is authenticated and is a super user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and user.is_superuser


class ActionNotAllowed(IsAuthenticated):
    """
    Checks if a user is authenticated and is a super user.
    """

    def has_permission(self, request, view):
        return False


# Connected user permissions
class CanChangeCurrentUser(IsAuthenticated):
    """
    Checks if a user has the permission to change a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_change_current_user(user)


class CanDeleteCurrentUser(IsAuthenticated):
    """
    Checks if a user has the permission to delete a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_delete_current_user(user)


class CanSoftDeleteCurrentUser(IsAuthenticated):
    """
    Checks if a user has the permission to soft delete a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_soft_delete_current_user(user)


# Permission Permissions
class CanSetPermission(IsAuthenticated):
    """
    Checks if a user has the permission to set permissions for other users.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_set_permission(user)


class CanExportPermissions(IsAuthenticated):
    """
    Checks if a user has the permission to export the list of permissions.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_export_permission(user)


# Log Entry Permissions
class CanListLogEntry(IsAuthenticated):
    """
    Checks if a user has the permission to view the activity journal.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_list_logentry(user)


class CanExportLogEntry(IsAuthenticated):
    """
    Checks if a user has the permission to export the activity journal.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_export_logentry(user)
