from django.utils.translation import gettext_lazy as _

from lava.models import Group
from lava.serializers.serializers import BaseModelSerializer, ReadOnlyModelSerializer


class GroupListSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "image",
        ]


class GroupGetSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "image",
            "parent",
            "permissions"
        ]


class GroupCreateUpdateSerializer(BaseModelSerializer):
    class Meta:
        model = Group
        fields = [
            "name",
            "description",
            "image",
            "parent",
            "permissions"
        ]
