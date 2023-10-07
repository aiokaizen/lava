from django.contrib.auth.forms import (
    UserChangeForm,
    AuthenticationForm,
    UserCreationForm,
)
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from lava import settings as lava_settings


class LavaUserChangeForm(UserChangeForm):
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
