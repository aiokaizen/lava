from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from lava.serializers.group_serializers import (
    GroupListSerializer,
    GroupGetSerializer,
    GroupCreateUpdateSerializer,
)
from lava.models import Group
from lava.views.api_views.base_api_views import BaseModelViewSet


class GroupAPIViewSet(BaseModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupListSerializer
    queryset = Group.objects.none()

    def get_serializer(self, *args, **kwargs):
        if self.action == "retrieve":
            self.serializer_class = GroupGetSerializer
        elif self.action in ["create", "update", "partial_update"]:
            self.serializer_class = GroupCreateUpdateSerializer
        return super().get_serializer(*args, **kwargs)
