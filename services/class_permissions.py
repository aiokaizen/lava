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
    Checks if a user has the permission to change a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_change_group(user)


class CanDeleteGroup(IsAuthenticated):
    """
    Checks if a user has the permission to delete a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_delete_group(user)


class CanSoftDeleteGroup(IsAuthenticated):
    """
    Checks if a user has the permission to soft delete a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_soft_delete_group(user)


class CanViewGroup(IsAuthenticated):
    """
    Checks if a user has the permission to view a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_view_group(user)


class CanListGroup(IsAuthenticated):
    """
    Checks if a user has the permission to view a list of groups.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_list_group(user)


class CanRestoreGroup(IsAuthenticated):
    """
    Checks if a user has the permission to restore a group.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_restore_group(user)


# User permissions
class CanAddUser(IsAuthenticated):
    """
    Checks if a user has the permission to create a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_add_user(user)


class CanChangeUser(IsAuthenticated):
    """
    Checks if a user has the permission to change a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_change_user(user)


class CanDeleteUser(IsAuthenticated):
    """
    Checks if a user has the permission to delete a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_delete_user(user)


class CanSoftDeleteUser(IsAuthenticated):
    """
    Checks if a user has the permission to soft delete a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_soft_delete_user(user)


class CanViewUser(IsAuthenticated):
    """
    Checks if a user has the permission to view a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_view_user(user)


class CanListUser(IsAuthenticated):
    """
    Checks if a user has the permission to view list of users.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_list_user(user)


class CanRestoreUser(IsAuthenticated):
    """
    Checks if a user has the permission to restore a user.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_restore_user(user)


# Permission Permissions
class CanExportPermissions(IsAuthenticated):
    """
    Checks if a user has the permission to export the list of permissions.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_export_permissions(user)


# Log Entry Permissions
class CanListLogEntry(IsAuthenticated):
    """
    Checks if a user has the permission to view the activity journal.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_list_log_entry(user)


class CanExportLogEntry(IsAuthenticated):
    """
    Checks if a user has the permission to export the activity journal.
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        user = request.user
        return is_authenticated and can_export_log_entry(user)
