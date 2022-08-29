from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.viewsets import ReadOnlyModelViewSet
from lava.messages import HTTP_403_MESSAGE

from lava.serializers import (
    ChangePasswordFormSerializer, UserSerializer,
    NotificationSerializer
)
from lava.models import Notification, User
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
        user = get_object_or_404(User, pk=kwargs.get('pk'))
        result = user.delete()
        return Response(result.to_dict(), status=status.HTTP_204_NO_CONTENT)



@api_view(('PUT', ))
@permission_classes((permissions.IsAdminUser, ))
def change_password(request, pk):
    instance = get_object_or_404(User, pk=pk)
    serializer = ChangePasswordFormSerializer(instance, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"ok": _("Password has been changed successfully!")})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(('GET', ))
@permission_classes((permissions.AllowAny, ))
def maintenance(request):
    data = {
        "maintenance_mode": True,
        "message": _(
            "This site is under maintenance. Our team is working hard "
            "to resolve the issues ASAP. Please come back later."
        )
    }
    return Response(data, status=status.HTTP_307_TEMPORARY_REDIRECT)


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
        return super().list(request, *args, **kwargs)
    
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
