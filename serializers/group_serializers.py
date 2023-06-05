from django.utils.translation import gettext_lazy as _

from lava.models import Group
from lava.serializers.base_serializers import BaseModelSerializer, ReadOnlyBaseModelSerializer
from lava.serializers.serializers import PermissionSerializer


class GroupListSerializer(ReadOnlyBaseModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


class GroupGetSerializer(ReadOnlyBaseModelSerializer):

    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "permissions"
        ]


class GroupCreateUpdateSerializer(BaseModelSerializer):

    m2m_field_names = ["permissions"]

    class Meta:
        model = Group
        fields = [
            "name",
            "permissions"
        ]
