from django.utils.translation import gettext_lazy as _

from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from lava.serializers.backup_serializers import (
    BackupSerializer
)
from lava.models import Backup
from lava.serializers import ResultSerializer
from lava.services import class_permissions as lava_permissions
from lava.views.api_views.base_api_views import BaseModelViewSet


class BackupAPIViewSet(BaseModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BackupSerializer
    queryset = Backup.objects.none()

    denied_actions = ["update", "retrieve"]

    @extend_schema(responses=ResultSerializer)
    @action(detail=True, methods=["POST"])
    def restore(self, request, *args, **kwargs):
        self.user = request.user
        obj = self.get_object()
        result = obj.restore_backup(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)
