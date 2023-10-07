from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import empty

from lava.models.utility_models import Address
from lava.serializers import BaseModelSerializer
from lava.models.organization_models import Bank


# Address serializer
class BankSerializer(BaseModelSerializer):
    class Meta:
        model = Bank
        fields = [
            "id",
            "name",
            "city",
            "agency",
            "country",
            "routing_number",
            "swift_code",
        ]
        read_only_fields = ["id"]
