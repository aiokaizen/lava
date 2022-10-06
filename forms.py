from django.contrib.auth.forms import UserChangeForm
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from lava import settings as lava_settings


class LavaUserChangeForm(UserChangeForm):
    def clean_groups(self):
        if "groups" in self.changed_data and self.instance.groups.all().count() == 1:
            group = self.instance.groups.all().first()
            model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
            if group.name in model_mapping.keys():
                raise ValidationError(_("You can't change the group for this user."))

        return self.cleaned_data["groups"]
