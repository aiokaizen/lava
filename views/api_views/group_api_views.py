from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from lava.serializers.group_serializers import (
    GroupListSerializer, GroupGetSerializer, GroupCreateUpdateSerializer
)
from lava.models import Group
from lava.services import class_permissions as lava_permissions


class GroupAPIViewSet(ModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupListSerializer
    queryset = Group.objects.none()

    def get_queryset(self):
        return Group.filter(user=self.user, kwargs=self.request.GET)
    
    def get_serializer(self, *args, **kwargs):
        if self.action == 'retrieve':
            self.serializer_class = GroupGetSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            self.serializer_class = GroupCreateUpdateSerializer

        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, user=self.user, **kwargs)

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        if self.action == 'create':
            permission_classes = [lava_permissions.CanAddGroup]
        if self.action == 'update':
            permission_classes = [lava_permissions.CanChangeGroup]
        if self.action == 'delete':
            permission_classes = [lava_permissions.CanSoftDeleteGroup]
        if self.action == 'retrieve':
            permission_classes = [lava_permissions.CanViewGroup]
        if self.action == 'list':
            permission_classes = [lava_permissions.CanListGroup]
        if self.action == 'restore':
            permission_classes = [lava_permissions.CanRestoreGroup]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        self.user = request.user
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.user = request.user
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        self.user = request.user
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        self.user = request.user
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        self.user = request.user
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        self.user = request.user
        object = self.get_object()
        result = object.delete(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result.to_dict(), status=status.HTTP_200_OK)
