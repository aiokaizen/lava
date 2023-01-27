from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from lava.serializers import ChangePasswordFormSerializer
from lava.serializers.user_serializers import (
    UserListSerializer, UserGetSerializer, UserCreateSerializer,
    UserUpdateSerializer, UserDeleteSerializer
)
from lava.models import User
from lava.services import class_permissions as lava_permissions
from lava.views.api_views.base_api_views import BaseModelViewSet


class UserAPIViewSet(BaseModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserListSerializer
    queryset = User.objects.none()

    def get_serializer(self, *args, **kwargs):
        if self.action == 'retrieve':
            self.serializer_class = UserGetSerializer
        elif self.action == 'create':
            self.serializer_class = UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            self.serializer_class = UserUpdateSerializer
        elif self.action == 'destroy':
            self.serializer_class = UserDeleteSerializer
        elif self.action == 'metadata' and self.detail :
            self.serializer_class = UserUpdateSerializer
        elif self.action == 'metadata' and not self.detail :
            self.serializer_class = UserCreateSerializer
        return super().get_serializer(*args, **kwargs)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [lava_permissions.CanAddUser]
        if self.action == 'update':
            self.permission_classes = [lava_permissions.CanChangeUser]
        if self.action == 'destroy':
            self.permission_classes = [lava_permissions.CanSoftDeleteUser]
        if self.action == 'retrieve':
            self.permission_classes = [lava_permissions.CanViewUser]
        if self.action == 'list':
            self.permission_classes = [lava_permissions.CanListUser]
        if self.action == 'restore':
            self.permission_classes = [lava_permissions.CanRestoreUser]
        return super().get_permissions()
    
    def destroy(self, request, *args, **kwargs):
        self.user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        result = user.delete(user=self.user, soft_delete=True)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def change_pwd(self, request, pk):
        self.user = request.user
        instance = self.get_object()
        serializer = ChangePasswordFormSerializer(
            instance, data=request.data, user=self.user
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": _("Password has been changed successfully!")
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
