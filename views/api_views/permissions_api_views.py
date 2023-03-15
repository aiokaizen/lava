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

    denied_actions = ["create", "destroy", "restore"]
