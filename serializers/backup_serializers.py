from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from lava.models import Backup
from lava.serializers.base_serializers import BaseModelSerializer


class BackupSerializer(BaseModelSerializer):

    class Meta:
        model = Backup
        fields = [
            "id",
            "name",
            "type",
            "status",
            "backup_file"
        ]
        read_only_fields = [
            "id",
            "name",
            "status",
            "backup_file"
        ]
