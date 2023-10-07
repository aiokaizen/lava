from django.utils.translation import gettext_lazy as _

from lava.serializers.log_entry_serializer import LogEntrySerializer
from lava.models.models import LogEntry
from lava.services import class_permissions as lava_permissions
from lava.views.api_views.base_api_views import ReadOnlyBaseModelViewSet


class LogEntryAPIViewSet(ReadOnlyBaseModelViewSet):

    permission_classes = [lava_permissions.CanListLogEntry]
    serializer_class = LogEntrySerializer
    queryset = LogEntry.objects.none()
