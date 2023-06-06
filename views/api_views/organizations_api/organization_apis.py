from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from lava.views.api_views.base_api_views import BaseModelViewSet
from lava.models.organization_models import Bank, BankAccount

from lava.serializers.organization_serializers import BankAccountSerializer,BankSerializer


# bank API View
class BankAPIViewSet(BaseModelViewSet):

    serializer_class = BankSerializer
    queryset = Bank.objects.none()

    denied_actions = [
        'view_trash', 'view_trash_item', 'restore', 'hard_delete'
    ]


# bank account API View
class BankAccountAPIViewSet(BaseModelViewSet):

    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.none()

    denied_actions = [
        'view_trash', 'view_trash_item', 'restore', 'hard_delete'
    ]


