from rest_framework.permissions import IsAuthenticated


# Notification permissions
def can_send_notifications(user):
    has_perm = user.has_perm('lava.send_notifications')
    return has_perm


# Group permissions
def can_add_group(user):
    has_perm = user.has_perm('lava.add_group')
    return has_perm


def can_change_group(user):
    has_perm = user.has_perm('lava.change_group')
    return has_perm


def can_delete_group(user):
    has_perm = user.has_perm('lava.delete_group')
    return has_perm


def can_soft_delete_group(user):
    has_perm = user.has_perm('lava.soft_delete_group')
    return has_perm


def can_view_group(user):
    has_perm = user.has_perm('lava.view_group')
    return has_perm


def can_list_group(user):
    has_perm = user.has_perm('lava.list_group')
    return has_perm


def can_restore_group(user):
    has_perm = user.has_perm('lava.restore_group')
    return has_perm


# User permissions
def can_add_user(user):
    has_perm = user.has_perm('lava.add_user')
    return has_perm


def can_change_user(user):
    has_perm = user.has_perm('lava.change_user')
    return has_perm


def can_delete_user(user):
    has_perm = user.has_perm('lava.delete_user')
    return has_perm


def can_soft_delete_user(user):
    has_perm = user.has_perm('lava.soft_delete_user')
    return has_perm


def can_view_user(user):
    has_perm = user.has_perm('lava.view_user')
    return has_perm


def can_list_user(user):
    has_perm = user.has_perm('lava.list_user')
    return has_perm


def can_restore_user(user):
    has_perm = user.has_perm('lava.restore_user')
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


# Permission permissions
def can_add_permission(user):
    has_perm = user.has_perm('lava.add_permission')
    return has_perm


def can_view_permission(user):
    has_perm = user.has_perm('lava.view_permission')
    return has_perm


def can_change_permission(user):
    has_perm = user.has_perm('lava.change_permission')
    return has_perm


def can_delete_permission(user):
    has_perm = user.has_perm('lava.delete_permission')
    return has_perm


def can_list_permission(user):
    has_perm = user.has_perm('lava.list_permission')
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
