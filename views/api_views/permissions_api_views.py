from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from lava.serializers.serializers import PermissionSerializer
from lava.models import Permission
from lava.services import class_permissions as lava_permissions
from lava.views.api_views.base_api_views import BaseModelViewSet


class PermissionAPIViewSet(BaseModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PermissionSerializer
    queryset = Permission.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [lava_permissions.CanAddPermission]
        if self.action == 'update':
            self.permission_classes = [lava_permissions.CanChangePermission]
        if self.action == 'destroy':
            self.permission_classes = [lava_permissions.CanDeletePermission]
        if self.action == 'retrieve':
            self.permission_classes = [lava_permissions.CanViewPermission]
        if self.action == 'list':
            self.permission_classes = [lava_permissions.CanListPermission]
        return super().get_permissions()
