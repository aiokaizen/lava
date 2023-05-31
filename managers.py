from django.db.models import Manager
from django.contrib.auth.models import UserManager

from lava import settings as lava_settings


class BaseModelManager(Manager):

    pass


class DefaultModelBaseManager(BaseModelManager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(deleted_at__isnull=True)
        return queryset



class DefaultModelTrashManager(BaseModelManager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(deleted_at__isnull=False)
        return queryset


class LavaUserManager(BaseModelManager, UserManager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(deleted_at__isnull=True)
        return queryset


class GroupManager(DefaultModelBaseManager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(notification_id='')
        if lava_settings.HIDE_ADMINS_GROUP:
            return queryset.exclude(name="ADMINS")
        return queryset


class NotificationGroupManager(DefaultModelBaseManager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(notification_id='')
        return queryset
