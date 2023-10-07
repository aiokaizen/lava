from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import empty

from lava.models.utility_models import Address
from lava.serializers import (
    ReadOnlyBaseModelSerializer,
    BaseModelSerializer,
    UserExerptSerializer,
)
from lava.models import BankAccount


# Address serializer
class BankAccountSerializer(BaseModelSerializer):
    class Meta:
        model = BankAccount
        fields = [
            "id",
            "name",
            "balance",
            "account_holder",
            "iban",
            "rib",
            "bank",
        ]
        read_only_fields = ["id"]
