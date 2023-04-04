from django.db.models import Manager
from django.contrib.auth.models import UserManager


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
        return queryset


class NotificationGroupManager(DefaultModelBaseManager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(notification_id='')
        return queryset
