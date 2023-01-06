from django.db.models import Q
from django.contrib.auth.models import UserManager


class LavaUserManager(UserManager):

    # def get_by_natural_key(self, username):
    #     criteria = get_search_criteria(username)
    #     return self.get(criteria)
    pass
