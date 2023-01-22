from rest_framework.permissions import IsAuthenticated

from lava.services.permissions import *


# Group PERMISSIONS
class CanAddGroup(IsAuthenticated):
    """
    Checks if a user has the permission to create a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_add_group(user)


class CanChangeGroup(IsAuthenticated):
    """
    Checks if a user has the permission to create a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_change_group(user)


class CanDeleteGroup(IsAuthenticated):
    """
    Checks if a user has the permission to create a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_delete_group(user)


class CanSoftDeleteGroup(IsAuthenticated):
    """
    Checks if a user has the permission to create a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_soft_delete_group(user)


class CanViewGroup(IsAuthenticated):
    """
    Checks if a user has the permission to create a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_view_group(user)


class CanListGroup(IsAuthenticated):
    """
    Checks if a user has the permission to create a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_list_group(user)


class CanRestoreGroup(IsAuthenticated):
    """
    Checks if a user has the permission to create a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_restore_group(user)


# Permission Permissions
class CanExportPermissions(IsAuthenticated):
    """
    Checks if a user has the permission to export the list of permissions.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_export_permissions(user)


# Activity Journal Permissions
class CanExportActivityJournal(IsAuthenticated):
    """
    Checks if a user has the permission to export the activity journal.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_export_activity_journal(user)
