from django.db.models import Manager
from django.contrib.auth.models import UserManager


class LavaUserManager(UserManager):

    # def get_by_natural_key(self, username):
    #     criteria = get_search_criteria(username)
    #     return self.get(criteria)
    pass


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
