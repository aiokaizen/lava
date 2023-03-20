from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.http import QueryDict
from django.apps import apps

from rest_framework import serializers
from rest_framework.fields import empty

from drf_spectacular.utils import extend_schema_field

from lava import settings as lava_settings
from lava.models import Preferences, User
from lava.models.models import Permission
from lava.serializers.base_serializers import BaseModelSerializer


class ResultSerializer(serializers.Serializer):

    class_name = serializers.CharField(label=_("Class name"), required=True)
    result = serializers.ChoiceField(
        label=_("Result"), choices=lava_settings.RESULT_TYPE_CHOICES, required=True
    )
    message = serializers.CharField(label=_("Message"), required=True)
    errors = serializers.DictField(label=_("Errors"), required=False)
    error_code = serializers.CharField(label=_("Error code"), required=False)
    object_id = serializers.IntegerField(label=_("Object ID"), required=False)

    class Meta:
        fields = [
            "class_name",
            "result",
            "message",
            "errors",
            "error_code",
            "object_id",
        ]


class ListIDsSerializer(serializers.Serializer):

    list_ids = serializers.ListField(label=_("IDs"), required=True)

    def __init__(self, instance=None, data=empty, model=None, trash=False, **kwargs):
        assert model is not None, (
            "Make sure that `model` parameter is different that None."
        )
        self.model = model
        self.trash = trash
        super().__init__(instance, data, **kwargs)

    def validate_list_ids(self, value):
        manager = self.model.trash if self.trash else self.model.objects
        try:
            qset = manager.filter(pk__in=value)
        except ValueError:
            raise serializers.ValidationError(_("One or more IDs is not valid."))

        if len(value) != qset.count():
            raise serializers.ValidationError(_("One or more IDs is not valid."))
        return qset


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
        required=True, label=_("Confirm new password"), write_only=True
    )

    class Meta:
        model = User
        fields = ("old_password", "new_password", "confirm_password")

    # Overriding the __init__ method just to make instance mandatory for this serializer
    def __init__(self, instance, data=empty, user=None, **kwargs):
        self.user = user
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
        result = instance.set_password(
            user=self.user, raw_password=validated_data["new_password"]
        )
        if result.is_error:
            raise serializers.ValidationError(
                result.errors or result.to_dict()
            )
        return instance


class PermissionSerializer(BaseModelSerializer):

    codename = serializers.SerializerMethodField(
        label=_("Code name")
    )

    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "codename"
        ]
        read_only_fields = [
            "id", "codename"
        ]

    @extend_schema_field(str)
    def get_codename(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}.{obj.codename}"


class ChoicesSerializer(serializers.Serializer):

    class_name = serializers.ChoiceField(label="Class name", choices=lava_settings.CLASS_NAME_CHOICES)
    query = serializers.CharField(label="Query")

    class Meta:
        fields = [
            'class_name',
            'query',
        ]
    
    def validate_query(self, value):
        if len(value) < 3:
            raise serializers.ValidationError(_("The query parametter must have a length of 3 or more."))
        return value

    def validate(self, data):
        validated_data = super().validate(data)
        class_name = lava_settings.CLASS_NAME_CHOICES_MAPPING[validated_data['class_name']]
        model = apps.get_model(*class_name.split('.'))
        query = validated_data['query']
        self.choices = [{
            "id": obj.pk,
            "label": getattr(obj, 'get_choices_display', lambda : None)() or str(obj),
        } for obj in model.filter(kwargs=QueryDict(f'query={query}'))]
        return validated_data
