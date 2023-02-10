from django.utils.translation import gettext_lazy as _

from lava.models import Backup
from lava.serializers.base_serializers import BaseModelSerializer


class BackupSerializer(BaseModelSerializer):

    class Meta:
        model = Backup
        fields = [
            "id",
            "type",
            "status",
            "backup_file"
        ]
        read_only_fields = [
            "id",
            "status",
            "backup_file"
        ]
