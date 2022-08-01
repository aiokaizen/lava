from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from rest_framework import permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status

from lava.serializers import ChangePasswordFormSerializer, UserSerializer
from lava.models import User


class UserListCreate(generics.ListCreateAPIView):
    """
    API endpoint that allows users to be listed or created.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that allows users to be viewed, edited, or deleted.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs.get('pk'))
        result = user.delete()
        return Response(result.to_dict(), status=status.HTTP_204_NO_CONTENT)



@api_view(('PUT', ))
@permission_classes((permissions.BasePermission, ))
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
