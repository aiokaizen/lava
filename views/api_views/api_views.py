from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, generics, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet

from lava.views.api_views.base_api_views import ReadOnlyBaseModelViewSet
from lava.messages import HTTP_403_MESSAGE
from lava.models import Notification, Preferences, User, NotificationGroup, Group
from lava.serializers import (
    PermissionSerializer,
    UserSerializer,
    NotificationSerializer,
    PreferencesSerializer,
)
from lava.serializers.serializers import ListIDsSerializer
from lava.serializers.group_serializers import GroupListSerializer
from lava.utils import Result
from lava.services.permissions import get_model_permission_class


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
            Result.error(_("'device_id' field is mandatory.")).to_dict(),
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    result = user.update_devices(device_id)
    return Response(result.to_dict())


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_user_permissions(request):
    user = request.user
    perms = user.get_all_permissions()
    serializer = PermissionSerializer(perms, many=True)
    return Response(serializer.data)


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


class NotificationGroupViewSet(ReadOnlyBaseModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupListSerializer
    permissions_model = Group
    queryset = NotificationGroup.objects.all()


class NotificationViewSet(ReadOnlyModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.none()

    def get_queryset(self):
        if not hasattr(self, 'user'):
            return self.queryset
        return self.user.get_notifications()

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        if self.action == "send_notification":
            permission_classes = [
                get_model_permission_class(Notification, 'add_notification')
            ]
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

    @action(detail=False, methods=["GET"])
    def unread(self, request, *args, **kwargs):
        self.user = request.user
        queryset = self.user.get_unread_notifications()
        unread_count = queryset.count()
        serializer = self.get_serializer(instance=queryset[:5], user=self.user, many=True)
        return Response({
            'notifications': serializer.data,
            'unread': unread_count
        })

    @action(detail=False, methods=["POST"])
    def mark_as_read(self, request, *args, **kwargs):
        user = request.user
        self.user = user
        serializer = ListIDsSerializer(data=request.data, model=Notification, trash=False)
        serializer.is_valid(raise_exception=True)
        queryset = serializer.validated_data["list_ids"]
        result = Notification.mark_as_read_bulk(queryset, self.user)
        if not result:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"])
    def send(self, request, *args, **kwargs):
        user = request.user
        self.user = user
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
