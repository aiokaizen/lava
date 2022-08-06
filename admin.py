from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from lava.forms import LavaUserChangeForm
from lava.models import Preferences, User, Group, Permission


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = LavaUserChangeForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
            'photo', 'first_name', 'last_name',
            'birth_day', 'gender', 'job', 'email',
            'phone_number', 'country', 'city', 'address',
        )}),
        (_('Preferences'), {
            'fields': ('cover_picture', 'preferences'),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    list_display = ('thumbnail', 'username', 'email', 'first_name', 'last_name', 'is_staff')

    def thumbnail(self, object):
        url = object.photo.url if object.photo else (
            '/static/ektools/assets/img/user_avatar.png'
        )
        style = f"""
            width: 30px; height: 30px; border-radius:50%; background-color: #fafafa;
            background-image: url({url}); background-position: center;
            background-size: cover;
        """
        return format_html(f'<div style="{style}"></div>')
    
    thumbnail.short_description = ''

    def save_model(self, request, obj, form, change):
        if not change:  # Creation
            photo = obj.photo
            cover = obj.cover_picture
            result = obj.create(photo, cover)
            if not result.success:
                raise Exception(result.message)
        elif obj is not None:  # Modification
            try:
                form.changed_data.remove('groups')
            except Exception:
                pass
            result = obj.update(update_fields=form.changed_data)
            if not result.success:
                raise Exception(result.message)
        

# @admin.register(Group)
# class GroupAdmin(admin.ModelAdmin):
#     pass


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Preferences)
class PreferencesAdmin(admin.ModelAdmin):
    pass
