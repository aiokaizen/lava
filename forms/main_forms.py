from django.contrib.auth.forms import UserChangeForm, AuthenticationForm, UserCreationForm
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from lava import settings as lava_settings


class LavaUserChangeForm(UserChangeForm):

    def clean_groups(self):
        if "groups" in self.changed_data and self.instance.groups.all().count() == 1:
            group = self.instance.groups.all().first()
            model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
            if group.name in model_mapping.keys():
                raise ValidationError(_("You can't change the group for this user."))

        return self.cleaned_data["groups"]
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LavaUserCreationForm(UserCreationForm):

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        # user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    pass


class SignupForm(UserCreationForm):
    pass
