from django.contrib.auth.models import UserManager
from django.apps import apps

from lava import settings as lava_settings


class LavaUserManager(UserManager):

    def create_user(self, username, email, password, **extra_fields):
        user = super().create_user(username, email, password, **extra_fields)
        model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
        for group in user.groups:
            if group.id in model_mapping.keys():
                app_label, class_name = model_mapping[group.id]
                klass = apps.get_model(app_label, class_name)
                klass(user_ptr=user)
                klass.save_base(raw=True)
        return user
