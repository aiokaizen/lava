from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from lava import settings as lava_settings
from lava.serializers.serializers import ChoicesSerializer
from lava.services.statistics import get_daily_actions, get_indicators, get_spaces, get_active_users, get_latest_actions


class ChoicesAPI(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):

        serializer = ChoicesSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.choices)


class DashboardAPIViewSet(ViewSet):

    permission_classes = [IsAuthenticated]
    
    @action(methods=['GET'], detail=False)
    def daily_actions(self, request):
        return Response(get_daily_actions())
    
    @action(methods=['GET'], detail=False)
    def indicators(self, request):
        return Response(get_indicators())
    
    @action(methods=['GET'], detail=False)
    def spaces(self, request):
        return Response(get_spaces())
    
    @action(methods=['GET'], detail=False)
    def active_users(self, request):
        return Response(get_active_users())

    @action(methods=['GET'], detail=False)
    def latest_actions(self, request):
        return Response(get_latest_actions())
    

class SettingsListAPI(APIView):

    permission_classes = [AllowAny]

    def get(self, request, format=None):
        settings = {}

        settings["GROUPS_NAMES"] = lava_settings.ALLOWED_SIGNUP_GROUPS

        return Response(data=settings, status=status.HTTP_200_OK)
