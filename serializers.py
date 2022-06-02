from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework.fields import empty

from lava.models import Preferences, User


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
            'id', 'last_login', 'date_joined'
        ]

    def __init__(self, instance=None, data=empty, **kwargs):
        if instance is None:
            self.Meta.extra_kwargs['photo'] = {'read_only': True}
            self.Meta.extra_kwargs['cover_picture'] = {'read_only': True}
        super().__init__(instance, data, **kwargs)
    
    def save(self, **kwargs):
        return super().save(**kwargs)
    