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


# Permission permissions
def can_export_permissions(user):
    return True
    # has_perm = user.has_perm('lava.export_permissions')
    # return has_perm


# ActivityJournal permissions
def can_export_activity_journal(user):
    return True
    # has_perm = user.has_perm('lava.export_permissions')
    # return has_perm
