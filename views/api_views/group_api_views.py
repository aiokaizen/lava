from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from lava.serializers.group_serializers import (
    GroupListSerializer, GroupGetSerializer, GroupCreateUpdateSerializer
)
from lava.models import Group
from lava.services import class_permissions as lava_permissions
from lava.views.api_views.base_api_views import BaseModelViewSet


class GroupAPIViewSet(BaseModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupListSerializer
    queryset = Group.objects.none()

    def get_serializer(self, *args, **kwargs):
        if self.action == 'retrieve':
            self.serializer_class = GroupGetSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            self.serializer_class = GroupCreateUpdateSerializer
        return super().get_serializer(*args, **kwargs)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [lava_permissions.CanAddGroup]
        if self.action == 'update':
            self.permission_classes = [lava_permissions.CanChangeGroup]
        if self.action == 'delete':
            self.permission_classes = [lava_permissions.CanSoftDeleteGroup]
        if self.action == 'retrieve':
            self.permission_classes = [lava_permissions.CanViewGroup]
        if self.action == 'list':
            self.permission_classes = [lava_permissions.CanListGroup]
        if self.action == 'restore':
            self.permission_classes = [lava_permissions.CanRestoreGroup]
        if self.action == "metadata":
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()
