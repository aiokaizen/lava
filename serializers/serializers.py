from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import empty

from lava import settings as lava_settings
from lava.models import Notification, Preferences, User, Group
from lava.models.models import Permission
from lava.validators import validate_email


class BaseModelSerializer(serializers.ModelSerializer):
    
    def __init__(self, instance=None, data=empty, user=None, **kwargs):
        self.user = user
        super().__init__(instance, data, **kwargs)

    def create(self, validated_data):

        m2m_field_names = getattr(self, 'm2m_field_names', [])
        m2m_fields = [] if m2m_field_names else None

        ModelClass = self.Meta.model
        instance = ModelClass()

        for attr, value in validated_data.items():
            if attr in m2m_field_names:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        result = instance.create(user=self.user, m2m_fields=m2m_fields)
        if result.is_error:
            raise serializers.ValidationError(result.errors or result.message)
        return instance
    
    def update(self, instance, validated_data):

        update_fields = []
        m2m_field_names = getattr(self, 'm2m_field_names', [])
        m2m_fields = []

        for attr, value in validated_data.items():
            if attr in m2m_field_names:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)
                update_fields.append(attr)

        result = instance.update(user=self.user, update_fields=update_fields, m2m_fields=m2m_fields)
        if result.is_error:
            raise serializers.ValidationError(result.errors or result.message)
        return self.instance


class ReadOnlyModelSerializer(BaseModelSerializer):

    _READ_ONLY_ERROR_MESSAGE = _("You can not create or update objects using a read-only serializer.")

    def save(self, *args, **kwargs):
        raise serializers.ValidationError(self._READ_ONLY_ERROR_MESSAGE)

    def create(self, *args, **kwargs):
        raise serializers.ValidationError(self._READ_ONLY_ERROR_MESSAGE)

    def update(self, *args, **kwargs):
        raise serializers.ValidationError(self._READ_ONLY_ERROR_MESSAGE)


class PreferencesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Preferences
        fields = [
            "font_style",
            "dark_theme",
            "list_layout",
            "menu_layout",
            "language",
            "notifications_settings",
        ]


class ChangePasswordFormSerializer(serializers.ModelSerializer):

    old_password = serializers.CharField(
        required=True, label=_("Current password"), write_only=True
    )
    new_password = serializers.CharField(
        required=True, label=_("New password"), write_only=True
    )
    confirm_password = serializers.CharField(
        required=False, label=_("Confirm new password"), write_only=True
    )

    class Meta:
        model = User
        fields = ("old_password", "new_password", "confirm_password")

    # Overriding the __init__ method just to make instance mandatory for this serializer
    def __init__(self, instance, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)

    def validate_old_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError(_("The current password does not match!"))

    def validate_new_password(self, value):
        validate_password(value, self.instance)
        return value

    def validate(self, data):
        pwd1 = data["new_password"]
        pwd2 = data["confirm_password"]

        if pwd1 != pwd2:
            raise serializers.ValidationError(
                {"confirm_password": _("Password confirmation is not valid!")}
            )
        return data

    def update(self, instance, validated_data):
        instance.update_password(validated_data["new_password"])
        return instance


class NotificationSerializer(serializers.ModelSerializer):

    sender = UserExerptSerializer(required=False)
    seen = serializers.SerializerMethodField(label=_("Seen"))

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "date",
            "title",
            "content",
            "category",
            "url",
            "target_groups",
            "target_users",
            "seen",
        ]
        read_only_fields = ["id", "sender", "date"]
        extra_kwargs = {
            "date": {
                "format": "%m/%d/%Y %H:%M:%S",
            },
            "writeonly_fields": [
                "target_groups",
                "target_users",
            ],
        }

    def __init__(self, user, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user

    def get_seen(self, instance):
        if not instance:
            return False
        return instance.seen(self.user)

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        target_groups = validated_data.get("target_groups")
        target_users = validated_data.get("target_users")
        if not target_groups and not target_users:
            raise serializers.ValidationError(
                _("You must specify either target groups or target users.")
            )
        return validated_data

    def create(self, validated_data):
        return self.user.send_notification(**validated_data)


class PermissionSerializer(serializers.ModelSerializer):

    codename = serializers.SerializerMethodField(
        label=_("Code name")
    )

    class Meta:
        model = Permission
        fields = [
            "name",
            "codename"
        ]
    
    def get_codename(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}.{obj.codename}"
