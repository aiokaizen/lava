from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group

from rest_framework import serializers
from rest_framework.fields import empty

from lava.models import Preferences, User
from lava import settings as lava_settings


class PreferencesSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Preferences
        fields = [
            'font_style', 'dark_theme',
            'list_layout', 'menu_layout', 'language',
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

        print(pwd1, pwd2)

        if pwd1 != pwd2:
            raise serializers.ValidationError(_("Password confirmation is not valid!"))
        return data

    def update(self, instance, validated_data):
        instance.update_password(validated_data['new_password'])
        return instance


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'username', 'photo', 'first_name', 'last_name',
            'birth_day', 'gender', 'job', 'email',
            'phone_number', 'country', 'city', 'address',
            'cover_picture', 'is_active', 'groups', 'last_login', 'date_joined'
        ]
        read_only_fields = [
            'id', 'is_active', 'last_login', 'date_joined'
        ]
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
            raise serializers.ValidationError(_("A user with that email already exists."))
        except User.DoesNotExist:
            return value
    
    def get_allowed_groups(self):
        group_list = [pk for pk, _ in lava_settings.ALLOWED_SIGNUP_GROUPS]
        return Group.objects.filter(pk__in=group_list)
    
    def validate_groups(self, value):
        allowed_groups = self.get_allowed_groups()
        allowed_groups_names = [name for _, name in lava_settings.ALLOWED_SIGNUP_GROUPS]
        for group in value:
            if group not in allowed_groups:
                raise serializers.ValidationError(
                    str(
                        _("Invalid group choice. Please choose from the following list:") + 
                        f" {allowed_groups_names}"
                    )
                )
        return value

    def create(self, validated_data):
        photo = validated_data.pop('photo')
        cover = validated_data.pop('cover_picture')
        instance = super().create(validated_data)
        instance.photo = photo
        instance.is_active = False
        instance.cover_picture = cover
        instance.save()
        return instance
    