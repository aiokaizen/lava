from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from rest_framework import permissions, generics, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet
from lava.messages import HTTP_403_MESSAGE

from lava.serializers import (
    ChangePasswordFormSerializer,
    UserSerializer,
    NotificationSerializer,
    PreferencesSerializer,
)
from lava.models import Notification, Preferences, User
from lava.utils import Result
from lava.services import permissions as lava_permissions


class UserListCreate(generics.ListCreateAPIView):
    """
    API endpoint that allows users to be listed or created.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that allows users to be viewed, edited, or deleted.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs.get("pk"))
        result = user.delete()
        return Response(result.to_dict(), status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def update_device_id(request):
    device_id = request.data.get("device_id")
    if not device_id:
        return Response(
            Result(False, _("'device_id' field is mandatory.")).to_dict(),
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    result = user.update_devices(device_id)
    return Response(result.to_dict())


class PreferencesViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Preferences.objects.none()
    serializer_class = PreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Preferences.objects.get(user=self.user)

    def list(self, request, *args, **kwargs):
        """
        This is used as the get() method because DRF SimpleRouter
        always maps get to list().
        # Try to create a custom router?
        """
        self.user = request.user
        preferences = self.get_object()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    def set(self, request):
        self.user = request.user
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(("PUT",))
@permission_classes((permissions.IsAdminUser,))
def change_password(request, pk):
    instance = get_object_or_404(User, pk=pk)
    serializer = ChangePasswordFormSerializer(instance, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"ok": _("Password has been changed successfully!")})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(ReadOnlyModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.none()

    def get_queryset(self):
        return self.user.get_notifications()

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        # if self.action == 'scan_ticket':
        #     permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        self.user = request.user
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(instance=page, user=self.user, many=True)
            response = self.get_paginated_response(serializer.data)

            # Mark all the notifications in the current page as read
            Notification.mark_as_read_bulk(page, self.user)

            return response

        serializer = self.get_serializer(instance=queryset, user=self.user, many=True)

        # Mark all the notifications as read
        Notification.mark_as_read_bulk(queryset, self.user)

        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    def send(self, request, *args, **kwargs):
        user = request.user
        self.user = user
        if not lava_permissions.can_send_notifications(user):
            return Response(HTTP_403_MESSAGE, status=status.HTTP_403_FORBIDDEN)
        serializer = NotificationSerializer(user=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.create(serializer.validated_data)
        if not result:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)


@api_view(("GET",))
@permission_classes((permissions.AllowAny,))
def maintenance(request):
    data = {
        "maintenance_mode": True,
        "message": _(
            "This site is under maintenance. Our team is working hard "
            "to resolve the issues as soon as possible. Please come back later."
        ),
    }
    return Response(data, status=status.HTTP_307_TEMPORARY_REDIRECT)
