from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from lava.serializers.user_serializers import (
    UserListSerializer, UserGetSerializer, UserCreateUpdateSerializer
)
from lava.models import User
from lava.utils import Result
from lava.services import class_permissions as lava_permissions


class UserAPIViewSet(ModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserListSerializer
    queryset = User.objects.none()

    def get_queryset(self):
        return User.filter(user=self.user, kwargs=self.request.GET)
    
    def get_serializer(self, *args, **kwargs):
        if self.action == 'retrieve':
            self.serializer_class = UserGetSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            self.serializer_class = UserCreateUpdateSerializer

        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, user=self.user, **kwargs)

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        if self.action == 'create':
            permission_classes = [lava_permissions.CanAddUser]
        if self.action == 'update':
            permission_classes = [lava_permissions.CanChangeUser]
        if self.action == 'delete':
            permission_classes = [lava_permissions.CanSoftDeleteUser]
        if self.action == 'retrieve':
            permission_classes = [lava_permissions.CanViewUser]
        if self.action == 'list':
            permission_classes = [lava_permissions.CanListUser]
        if self.action == 'restore':
            permission_classes = [lava_permissions.CanRestoreUser]
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

        user_password = request.data.get('password')
        if not user_password:
            result = Result(False, _("Please enter your password and try again."))
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)

        if not self.user.check_password(user_password):
            result = Result(False, _("Incorrect password, please verify that 'All caps' is disabled."))
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)

        user = self.get_object()
        result = user.delete(user=self.user, soft_delete=True)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def restore(self, request, pk):
        self.user = request.user
        user = get_object_or_404(User.trash.all(), pk=pk)
        result = user.restore(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def change_password(self, request, pk):
        pass
