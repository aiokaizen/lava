from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from lava.serializers.backup_serializers import (
    BackupSerializer
)
from lava.models import Backup
from lava.services import class_permissions as lava_permissions
from lava.views.api_views.base_api_views import BaseModelViewSet


class BackupAPIViewSet(BaseModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BackupSerializer
    queryset = Backup.objects.none()

    denied_actions = ["update", "restore", "retrieve", "metadata"]

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [lava_permissions.CanAddGroup]
        if self.action == 'delete':
            self.permission_classes = [lava_permissions.CanSoftDeleteGroup]
        if self.action == 'list':
            self.permission_classes = [lava_permissions.CanListGroup]
        return super().get_permissions()
