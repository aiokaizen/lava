from django.db.models import Manager
from django.contrib.auth.models import UserManager

from lava import settings as lava_settings


class LavaUserManager(UserManager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(deleted_at__isnull=True)
        return queryset


class DefaultBaseModelManager(Manager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(deleted_at__isnull=True)
        return queryset


class TrashBaseModelManager(Manager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(deleted_at__isnull=False)
        return queryset


class GroupManager(Manager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(name__startswith=lava_settings.NOTIFICATION_GROUP_PREFIX)
        return queryset


class NotificationGroupManager(Manager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(name__startswith=lava_settings.NOTIFICATION_GROUP_PREFIX)
        return queryset
