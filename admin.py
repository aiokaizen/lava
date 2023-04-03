from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin
from django.contrib.auth.models import (
    Group as BaseGroupModel
)
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from rest_framework.authtoken.admin import TokenAdmin

from admin_interface.models import Theme

from lava.forms.main_forms import LavaUserChangeForm
from lava.models import (
    Notification, Preferences, User, Group, Backup,
    Conversation, ChatMessage
)
from lava.utils.utils import pop_list_item


# Unregister models
admin.site.unregister(BaseGroupModel)
admin.site.unregister(Theme)


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
                    "street_address",
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
        (_("Important dates"), {"fields": ("last_login", "date_joined", "deleted_at")}),
    )
    readonly_fields = [
        "tmp_pwd", "last_login", "date_joined", "deleted_at",
        "is_superuser"
    ]

    list_display = (
        "thumbnail",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
    )

    actions = [
        "link_to_payments"
    ]

    def thumbnail(self, obj):
        url = (
            obj.photo.url
            if obj.photo
            else "/static/ektools/assets/img/user_avatar.png"
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
            obj.photo = None
            obj.cover = None
            result = obj.create(
                user=request.user, file_fields=(('photo', photo), ('cover', cover))
            )
            if not result.is_success:
                raise Exception(result.message)
        elif obj is not None:  # Modification
            # Remove groups and user_permissions from changed_data because .save() method does not accept related fields
            # to be passed in the update_fields parameter.
            pop_list_item(form.changed_data, 'groups')
            pop_list_item(form.changed_data, 'user_permissions')

            result = obj.update(user=request.user, update_fields=form.changed_data)
            if not result.success:
                raise Exception(result.message)

    @admin.action(description='Link to payments')
    def link_to_payments(self, request, queryset):
        for user in queryset:
            result = user.link_payments_app()
            if not result.success:
                lvl = messages.ERROR if result.is_error else messages.WARNING
                self.message_user(
                    request,
                    (
                        f"The following error rose while trying to link the user '{user}' "
                        f"to the payments app: \n\t{result.message}"
                    ),
                    lvl
                )

        self.message_user(request, "The selected users were successfully linked to payments.", messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        for user in queryset:
            result = user.delete()
            if not result.success:
                lvl = messages.ERROR if result.is_error else messages.WARNING
                self.message_user(
                    request,
                    f"The following error rose while deleting the user '{user}': \n\t{result.message}",
                    lvl
                )

        self.message_user(request, "The selected users were successfully deleted.", messages.SUCCESS)

    def get_queryset(self, request):
        return User.filter(user=request.user, kwargs=request.GET)


class BaseModelAdmin(admin.ModelAdmin):

    m2m_field_names = []
    file_field_names = []

    fieldsets = (
        (
            _("Base attributes"),
            {
                "classes": ("collapse", "expanded"),
                "fields": (
                    "created_at",
                    "created_by",
                    "last_updated_at",
                    "deleted_at"
                ),
            },
        ),
    )

    readonly_fields = [
        "created_at",
        "created_by",
        "last_updated_at",
        "deleted_at"
    ]

    actions = [
        "soft_delete",
        "restore"
    ]

    def save_related(self, request, form, formsets, change):
        # Desable save related behaviour, since we save our related
        # fields using the create() method.

        # return super().save_related(request, form, formsets, change)
        pass

    def save_model(self, request, obj, form, change):
        if not change:  # Creation
            result = self.create(request.user, obj, form.cleaned_data)
            if not result.is_success:
                lvl = messages.ERROR if result.is_error else messages.WARNING
                self.message_user(
                    request,
                    result.message,
                    lvl
                )
        elif obj is not None:  # Modification
            result = self.update(request.user, obj, form.changed_data, form.cleaned_data)
            if not result.is_success:
                lvl = messages.ERROR if result.is_error else messages.WARNING
                self.message_user(
                    request,
                    result.message,
                    lvl
                )

    def create(self, user, obj, validated_data, **kwargs):

        m2m_field_names = getattr(self, 'm2m_field_names', [])
        m2m_fields = [] if m2m_field_names else None

        file_field_names = getattr(self, 'file_field_names', [])
        file_fields = [] if file_field_names else None

        for attr, value in validated_data.items():
            if attr in m2m_field_names:
                m2m_fields.append((attr, value))
            elif attr in file_field_names:
                file_fields.append((attr, value))
                setattr(obj, attr, None)

        return obj.create(
            user=user, m2m_fields=m2m_fields, file_fields=file_fields, **kwargs
        )

    def update(self, user, obj, update_fields, validated_data, **kwargs):

        m2m_field_names = getattr(self, 'm2m_field_names', [])
        m2m_fields = []

        for attr, value in validated_data.items():
            if attr in m2m_field_names:
                m2m_fields.append((attr, value))

        return obj.update(user=user, update_fields=update_fields, m2m_fields=m2m_fields, **kwargs)


    @admin.action(description=_('Soft delete'))
    def soft_delete(self, request, queryset):
        for obj in queryset:
            result = obj.soft_delete(user=request.user)
            if not result.is_success:
                lvl = messages.ERROR if result.is_error else messages.WARNING
                self.message_user(
                    request,
                    _(
                        "The following error rose while trying "
                        "to delete '%(obj)s': \n\t%(msg)s" % {
                            'obj': obj,
                            'msg': result.message
                        }
                    ),
                    lvl
                )

        self.message_user(request, _("The selected objects were successfully deleted."), messages.SUCCESS)

    @admin.action(description=_('Restore'))
    def restore(self, request, queryset):
        for obj in queryset:
            result = obj.restore(user=request.user)
            if not result.is_success:
                lvl = messages.ERROR if result.is_error else messages.WARNING
                self.message_user(
                    request,
                    _(
                        "The following error rose while trying "
                        "to restore '%(obj)s': \n\t%(msg)s" % {
                            'obj': obj,
                            'msg': result.message
                        }
                    ),
                    lvl
                )

        self.message_user(
            request, _("The selected objects were successfully restored."),
            messages.SUCCESS
        )

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            result = obj.delete(user=request.user, soft_delete=False)
            if not result.is_success:
                lvl = messages.ERROR if result.is_error else messages.WARNING
                self.message_user(
                    request,
                    _("The following error rose while deleting '%(obj)s': \n\t%(msg)s" % {
                        'obj': obj,
                        'msg': result.message
                    }),
                    lvl
                )

        self.message_user(request, _("The selected objects were successfully deleted."), messages.SUCCESS)

    def get_queryset(self, request):
        return self.model.filter(user=request.user, kwargs=request.GET)


@admin.register(Group)
class GroupAdmin(BaseModelAdmin):
    pass


@admin.register(Backup)
class BackupAdmin(BaseModelAdmin):
    pass


@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    m2m_field_names = ['target_users', 'target_groups']
    file_field_names = []
    fieldsets = None
    readonly_fields = ()
    icon_name = "notifications"


@admin.register(Preferences)
class PreferencesAdmin(admin.ModelAdmin):
    pass


@admin.register(Conversation)
class ConversationAdmin(BaseModelAdmin):
    pass


@admin.register(ChatMessage)
class ChatMessageAdmin(BaseModelAdmin):
    pass
