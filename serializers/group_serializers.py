from django.utils.translation import gettext_lazy as _

from lava.models import Group
from lava.serializers.serializers import BaseModelSerializer, ReadOnlyModelSerializer


class GroupListSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


class GroupGetSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "permissions"
        ]


class GroupCreateUpdateSerializer(BaseModelSerializer):
    class Meta:
        model = Group
        fields = [
            "name",
            "permissions"
        ]
