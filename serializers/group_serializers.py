from django.utils.translation import gettext_lazy as _

from lava.models import Group
from lava.serializers.base_serializers import BaseModelSerializer, ReadOnlyModelSerializer
from lava.serializers.serializers import PermissionSerializer


class GroupListSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


class GroupGetSerializer(ReadOnlyModelSerializer):

    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "permissions"
        ]


class GroupCreateUpdateSerializer(BaseModelSerializer):

    permissions = PermissionSerializer(many=True, required=False)

    class Meta:
        model = Group
        fields = [
            "name",
            "permissions"
        ]
