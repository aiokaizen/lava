from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework import serializers

from lava import settings as lava_settings
from lava.models import User, Group
from lava.serializer_fields import ThumbnailImageField
from lava.serializers.serializers import PermissionSerializer
from lava.serializers.base_serializers import (
    BaseModelSerializer, ReadOnlyBaseModelSerializer
)
from lava.serializers.group_serializers import GroupListSerializer
from lava.validators import validate_email


class UserExerptSerializer(ReadOnlyBaseModelSerializer):
    class Meta:
        model = User
        fields = ["id", "photo", "username", "first_name", "last_name"]

    def save(self, **kwargs):
        raise serializers.ValidationError(
            _("You can't create or update objects using a read-only serializer.")
        )


class UserListSerializer(ReadOnlyBaseModelSerializer):

    photo = ThumbnailImageField(alias='thumbnail')

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "photo",
            "first_name",
            "last_name",
            "job",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
        ]


class UserGetSerializer(ReadOnlyBaseModelSerializer):

    groups = GroupListSerializer(many=True)
    user_permissions = PermissionSerializer(many=True)
    permissions = PermissionSerializer(many=True, source="get_all_permissions")
    photo = ThumbnailImageField(alias='avatar')
    cover_picture = ThumbnailImageField(alias='cover')

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
            "street_address",
            "cover_picture",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "permissions",
            "last_login",
            "date_joined",
        ]
        extra_kwargs = {
            "birth_day": {"format": "%m/%d/%Y"},
            "last_login": {"format": "%m/%d/%Y %H:%M:%S"},
            "date_joined": {"format": "%m/%d/%Y %H:%M:%S"},
        }


class UserCreateSerializer(BaseModelSerializer):

    confirm_password = serializers.CharField(
        label=_("Password confirmation"), required=False
    )

    class Meta:
        model = User
        fields = [
            "username",
            "photo",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "password",
            "confirm_password",
        ]

    def validate_password(self, value):
        validate_password(value, User)
        return value

    def validate(self, data):
        validated_data = super().validate(data)
        pwd1 = validated_data["password"]
        pwd2 = validated_data.get("confirm_password")

        if pwd1 != pwd2:
            raise serializers.ValidationError(
                {"confirm_password": _("Password confirmation is not valid!")}
            )
        return validated_data

    def create(self, validated_data):
        photo = validated_data.pop("photo", None)
        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        instance = User(**validated_data)
        self.result = instance.create(
            user=self.user, photo=photo, password=password
        )
        if not self.result.success:
            raise serializers.ValidationError(
                self.result.errors or self.result.message
            )
        return instance

    def update(self, instance, validated_data):
        raise serializers.ValidationError(
            _("You can not update a user using this serializer.")
        )


class UserUpdateSerializer(BaseModelSerializer):

    m2m_field_names = ['groups', 'user_permissions']

    class Meta :
        model = User
        fields = [
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
            "street_address",
            "cover_picture",
            "is_active",
            "is_staff",
            "groups",
            "user_permissions",
        ]
        extra_kwargs = {
            "birth_day": {
                "format": "%m/%d/%Y",
                "input_formats": settings.DATE_INPUT_FORMATS,
            },
            "last_login": {"format": "%m/%d/%Y %H:%M:%S"},
            "date_joined": {"format": "%m/%d/%Y %H:%M:%S"},
        }

    def validate(self, value):
        validated_data = super().validate(value)
        email = validated_data.get("email")
        groups = validated_data.get("groups")

        if email:
            try:
                validated_data["email"] = validate_email(email, groups)
            except ValidationError as e:
                raise serializers.ValidationError({"email": e.message})

        return validated_data

    def create(self, validated_data):
        raise serializers.ValidationError(
            _("You can not create a user using this serializer.")
        )


class UserProfileUpdateSerializer(BaseModelSerializer):

    class Meta :
        model = User
        fields = [
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
            "street_address",
            "cover_picture",
        ]
        extra_kwargs = {
            "birth_day": {
                "format": "%m/%d/%Y",
                "input_formats": settings.DATE_INPUT_FORMATS,
            }
        }

    def validate(self, value):
        validated_data = super().validate(value)
        email = validated_data.get("email")
        groups = self.instance.groups.all()

        if email:
            try:
                validated_data["email"] = validate_email(email, groups)
            except ValidationError as e:
                raise serializers.ValidationError({"email": e.message})

        return validated_data

    def create(self, validated_data):
        raise serializers.ValidationError(
            _("You can not create a user using this serializer.")
        )


class UserDeleteSerializer(ReadOnlyBaseModelSerializer):

    current_password = serializers.CharField(label="Password", required=True)

    class Meta:
        model = User
        fields = [
            "current_password",
        ]

    def validate_current_password(self, value):
        if not self.user.check_password(value):
            raise serializers.ValidationError(
                _("Incorrect password, please verify that 'All caps' is disabled.")
            )
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    This serializer was created for Djoser APIs.
    """

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
            "street_address",
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
        user = getattr(self, 'user', None)
        result = instance.create(
            user=user, photo=photo, cover=cover, groups=groups, password=password, extra_attributes=extra_attributes
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
