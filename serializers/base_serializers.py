from copy import deepcopy, copy

from django.utils.translation import gettext_lazy as _
from django.db import models

from rest_framework import serializers
from rest_framework.fields import empty


class BaseModelSerializer(serializers.ModelSerializer):

    m2m_field_names = []
    file_field_names = []

    def __init__(self, instance=None, data=empty, user=None, **kwargs):
        self.user = user
        super().__init__(instance, data, **kwargs)

    def to_internal_value(self, data):
        data = deepcopy(data)
        for m2m_field_name in self.m2m_field_names:
            if m2m_field_name in data and data[m2m_field_name] == "null":
                data.setlist(m2m_field_name, [])
        return super().to_internal_value(data)
    
    def create(self, validated_data, **kwargs):

        m2m_field_names = getattr(self, 'm2m_field_names', [])
        m2m_fields = [] if m2m_field_names else None

        file_field_names = getattr(self, 'file_field_names', [])
        file_fields = [] if file_field_names else None

        ModelClass = self.Meta.model
        instance = ModelClass()

        for attr, value in validated_data.items():
            if attr in m2m_field_names:
                m2m_fields.append((attr, value))
            elif attr in file_field_names:
                file_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        self.result = instance.create(
            user=self.user, m2m_fields=m2m_fields, file_fields=file_fields, **kwargs
        )
        if self.result.is_error and self.result.errors:
            raise serializers.ValidationError(self.result.errors or self.result.message, self.result.error_code)
        return instance

    def update(self, instance, validated_data, **kwargs):

        update_fields = []
        m2m_field_names = getattr(self, 'm2m_field_names', [])
        m2m_fields = []

        for attr, value in validated_data.items():
            if attr in m2m_field_names:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)
                update_fields.append(attr)

        self.result = instance.update(user=self.user, update_fields=update_fields, m2m_fields=m2m_fields, **kwargs)
        if self.result.is_error:
            raise serializers.ValidationError(self.result.errors or self.result.message, self.result.error_code)
        return instance


class ReadOnlyBaseModelSerializer(BaseModelSerializer):

    _READ_ONLY_ERROR_MESSAGE = _("You can not create or update objects using a read-only serializer.")

    def save(self, *args, **kwargs):
        raise serializers.ValidationError(self._READ_ONLY_ERROR_MESSAGE)

    def create(self, *args, **kwargs):
        raise serializers.ValidationError(self._READ_ONLY_ERROR_MESSAGE)

    def update(self, *args, **kwargs):
        raise serializers.ValidationError(self._READ_ONLY_ERROR_MESSAGE)
