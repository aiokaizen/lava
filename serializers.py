from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import empty

from lava import settings as lava_settings
from lava.models import Notification, Preferences, User, Group
from lava.validators import validate_email


class ReadOnlyModelSerializer(serializers.ModelSerializer):
    def save(self, **kwargs):
        raise serializers.ValidationError(
            _("You can't create or update objects using a read-only serializer.")
        )


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


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name"]


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


class UserExerptSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = User
        fields = ["id", "photo", "first_name", "last_name"]

    def save(self, **kwargs):
        raise serializers.ValidationError(
            _("You can't create or update objects using a read-only serializer.")
        )


class UserSerializer(serializers.ModelSerializer):

    groups_names = serializers.ListField(label=_("Groups"), required=True)
    extra_attributes = serializers.JSONField(
        label=_("Extra attributes"),
        required=False,
        help_text=_(
            "Attributes related to an object that is related to the current user."
        ),
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
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
            "cover_picture",
            "is_active",
            "groups_names",
            "last_login",
            "date_joined",
            "extra_attributes",
            "password",
        ]
        read_only_fields = ["id", "is_active", "last_login", "date_joined"]
        extra_kwargs = {
            "extra_attributes": {"write_only": True},
            "password": {"write_only": True},
            "birth_day": {
                "format": "%m/%d/%Y",
                "input_formats": settings.DATE_INPUT_FORMATS,
            },
            "last_login": {"format": "%m/%d/%Y %H:%M:%S"},
            "date_joined": {"format": "%m/%d/%Y %H:%M:%S"},
        }

    def validate(self, value):
        validated_data = super().validate(value)
        groups_names = validated_data.get("groups_names")
        email = validated_data.get("email")
        if isinstance(groups_names, list):
            groups = Group.objects.filter(name__in=groups_names)
        else:
            groups = groups_names

        if email:
            try:
                validated_data["email"] = validate_email(email, groups)
            except ValidationError as e:
                raise serializers.ValidationError({"email": e.message})

        return validated_data

    def validate_password(self, value):
        validate_password(value, User)
        return value

    def get_allowed_groups(self):
        group_list = [name.upper() for name, _ in lava_settings.ALLOWED_SIGNUP_GROUPS]
        return Group.objects.filter(name__in=group_list)

    def validate_groups_names(self, value):
        groups_names = []
        for gn in value:
            if not isinstance(gn, str):
                raise serializers.ValidationError(
                    _("groups names must be a list of names.")
                )
            groups_names.append(gn.upper())
        allowed_groups = self.get_allowed_groups().values_list("name", flat=True)
        for group_name in groups_names:
            if group_name not in allowed_groups:
                raise serializers.ValidationError(_("Invalid group choice."))
        return Group.objects.filter(name__in=groups_names)

    def create(self, validated_data):
        photo = validated_data.pop("photo", None)
        cover = validated_data.pop("cover_picture", None)
        groups = validated_data.pop("groups_names", None)
        password = validated_data.pop("password", None)
        extra_attributes = validated_data.pop("extra_attributes", None)
        instance = User(**validated_data)
        result = instance.create(
            photo, cover, groups, password=password, extra_attributes=extra_attributes
        )
        if not result.success:
            raise serializers.ValidationError(result.to_dict())
        return instance

    def update(self, instance, validated_data):
        extra_attributes = validated_data.pop("extra_attributes", None)
        update_fields = validated_data.keys()
        for key, value in validated_data.items():
            setattr(instance, key, value)
        result = instance.update(
            update_fields=update_fields, extra_attributes=extra_attributes
        )
        if not result.success:
            raise serializers.ValidationError(result.as_dict())
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
