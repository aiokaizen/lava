from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from lava import settings as lava_settings
from lava.serializers.serializers import ChoicesSerializer
from lava.services.statistics import collect_statistics


class ChoicesAPI(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):

        serializer = ChoicesSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.choices)


class DashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):

        return Response(collect_statistics())


class SettingsListAPI(APIView):

    permission_classes = [AllowAny]

    def get(self, request, format=None):
        settings = {}

        settings["GROUPS_NAMES"] = lava_settings.ALLOWED_SIGNUP_GROUPS

        return Response(data=settings, status=status.HTTP_200_OK)
