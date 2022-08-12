from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.conf import settings

from rest_framework import serializers
from rest_framework.fields import empty

from lava.models import Preferences, User, Group
from lava import settings as lava_settings


class PreferencesSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Preferences
        fields = [
            'font_style', 'dark_theme',
            'list_layout', 'menu_layout', 'language',
        ]


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = [
            'name'
        ]


class ChangePasswordFormSerializer(serializers.ModelSerializer):

    old_password = serializers.CharField(required=True, label=_("Current password"), write_only=True)
    new_password = serializers.CharField(required=True, label=_("New password"), write_only=True)
    confirm_password = serializers.CharField(required=False, label=_("Confirm new password"), write_only=True)

    class Meta:
        model = User
        fields = (
            'old_password', 'new_password', 'confirm_password'
        )
    
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
        pwd1 = data['new_password']
        pwd2 = data['confirm_password']

        if pwd1 != pwd2:
            raise serializers.ValidationError(
                {"confirm_password": _("Password confirmation is not valid!")}
            )
        return data

    def update(self, instance, validated_data):
        instance.update_password(validated_data['new_password'])
        return instance


class UserSerializer(serializers.ModelSerializer):

    groups_names = serializers.ListField(
        label=_("Groups"), required=True
    )
    extra_attributes = serializers.JSONField(
        label=_("Extra attributes"), required=False,
        help_text=_("Attributes related to an object that is related to the current user.")
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'photo', 'first_name', 'last_name',
            'birth_day', 'gender', 'job', 'email',
            'phone_number', 'country', 'city', 'address',
            'cover_picture', 'is_active', 'groups_names', 'last_login', 'date_joined',
            'extra_attributes', 'password',
        ]
        read_only_fields = [
            'id', 'is_active', 'last_login', 'date_joined'
        ]
        extra_kwargs = {
            "extra_attributes": {"write_only": True},
            "password": {"write_only": True},
            "birth_day": {
                "format": "%m/%d/%Y",
                "input_formats": settings.DATE_INPUT_FORMATS
            },
            "last_login": {"format": "%m/%d/%Y %H:%M:%S"},
            "date_joined": {"format": "%m/%d/%Y %H:%M:%S"},
        }
    
    def validate(self, value):
        validated_data = super().validate(value)
        groups_names = validated_data.get('groups_names')
        if isinstance(groups_names, list):
            groups = Group.objects.filter(name__in=groups_names)
        else:
            groups = groups_names
        
        if groups and (
            lava_settings.EMAIL_GROUP_UNIQUE_TOGETHER and
            not lava_settings.DENY_DUPLICATE_EMAILS
        ):
            try:
                User.objects.get(email=value, groups__in=groups)
                raise serializers.ValidationError(
                    {"email": _("A user with that email already exists.")}
                )
            except User.DoesNotExist:
                return validated_data
        
        return validated_data
     
    def validate_email(self, value):
        if not lava_settings.DENY_DUPLICATE_EMAILS:
            return value

        try:
            User.objects.get(email=value)
            raise serializers.ValidationError(_("A user with that email already exists."))
        except User.DoesNotExist:
            return value
 
    def validate_password(self, value):
            validate_password(value, User)
    
    def get_allowed_groups(self):
        group_list = [name.upper() for name, _ in lava_settings.ALLOWED_SIGNUP_GROUPS]
        return Group.objects.filter(name__in=group_list)
    
    def validate_groups_names(self, value):
        groups_names = []
        for gn in value:
            if not isinstance(gn, str):
                raise serializers.ValidationError(_("groups names must be a list of names."))
            groups_names.append(gn.upper())
        allowed_groups = self.get_allowed_groups().values_list('name', flat=True)
        for group_name in groups_names:
            if group_name not in allowed_groups:
                raise serializers.ValidationError(_("Invalid group choice."))
        return Group.objects.filter(name__in=groups_names)

    def create(self, validated_data):
        photo = validated_data.pop('photo', None)
        cover = validated_data.pop('cover_picture', None)
        groups = validated_data.pop('groups_names', None)
        password = validated_data.pop('password', None)
        extra_attributes = validated_data.pop("extra_attributes", None)
        instance = User(**validated_data)
        result = instance.create(
            photo, cover, groups,
            password=password, extra_attributes=extra_attributes
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
 