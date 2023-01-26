from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from lava import settings as lava_settings


class SettingsList(APIView):

    permission_classes = [AllowAny]

    def get(self, request, format=None):
        settings = {}

        settings["GROUPS_NAMES"] = lava_settings.ALLOWED_SIGNUP_GROUPS

        return Response(data=settings, status=status.HTTP_200_OK)
