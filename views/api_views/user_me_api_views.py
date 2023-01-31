from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from djoser import utils

from lava.serializers.user_serializers import (
    UserGetSerializer, UserUpdateSerializer, UserDeleteSerializer
)
from lava.services import class_permissions as lava_permissions


class UserMeAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            self.permission_classes = [lava_permissions.CanChangeCurrentUser]
        elif self.request.method == 'DELETE':
            self.permission_classes = [lava_permissions.CanSoftDeleteCurrentUser]
        return super().get_permissions()
    
    def get(self, request):
       user = request.user
       serializer = UserGetSerializer(user, user=user) 
       return Response(serializer.data)
    
    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user = request.user
        serializer = UserUpdateSerializer(
            instance=user, data=request.data, user=user, partial=partial
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()
        result = serializer.result
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    def patch(self, request):
        return self.put(request, partial=True)
    
    def delete(self, request):
        user = request.user
        serializer = UserDeleteSerializer(data=request.data, user=user)
        serializer.is_valid(raise_exception=True)
        result = user.delete(user=user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        utils.logout_user(request)
        return Response(result.to_dict(), status=status.HTTP_200_OK)
