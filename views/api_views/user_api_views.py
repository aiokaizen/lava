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

    list_serializer_class = UserListSerializer
    retrieve_serializer_class = UserGetSerializer
    create_serializer_class = UserCreateSerializer
    update_serializer_class = UserUpdateSerializer
    delete_serializer_class = UserDeleteSerializer

    queryset = User.objects.none()

    def get_permissions(self):
        if self.action == 'me' or getattr(self, 'is_me', False):
            self.permission_classes = [permissions.IsAuthenticated]

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
