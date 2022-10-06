from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from lava.forms import LavaUserChangeForm
from lava.models import Notification, Preferences, User, Group, Permission


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = LavaUserChangeForm
    fieldsets = (
        (None, {"fields": ("username", "password", "tmp_pwd")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "photo",
                    "first_name",
                    "last_name",
                    "birth_day",
                    "gender",
                    "job",
                    "email",
                    "phone_number",
                    "country",
                    "city",
                    "address",
                    "device_id_list",
                )
            },
        ),
        (
            _("Preferences"),
            {
                "fields": ("cover_picture", "preferences"),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ["tmp_pwd"]

    list_display = (
        "thumbnail",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
    )

    def thumbnail(self, object):
        url = (
            object.photo.url
            if object.photo
            else ("/static/ektools/assets/img/user_avatar.png")
        )
        style = f"""
            width: 30px; height: 30px; border-radius:50%; background-color: #fafafa;
            background-image: url({url}); background-position: center;
            background-size: cover;
        """
        return format_html(f'<div style="{style}"></div>')

    thumbnail.short_description = ""

    def save_model(self, request, obj, form, change):
        if not change:  # Creation
            photo = obj.photo
            cover = obj.cover_picture
            result = obj.create(photo, cover)
            if not result.success:
                raise Exception(result.message)
        elif obj is not None:  # Modification
            if "groups" in form.changed_data:
                # Remove groups from changed_data because .save() method does not accept related fields
                # to be passed in the update_fields parameter.
                form.changed_data.remove("groups")
            result = obj.update(update_fields=form.changed_data)
            if not result.success:
                raise Exception(result.message)


# @admin.register(Group)
# class GroupAdmin(admin.ModelAdmin):
#     pass


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    icon_name = "notifications"


@admin.register(Preferences)
class PreferencesAdmin(admin.ModelAdmin):
    pass
