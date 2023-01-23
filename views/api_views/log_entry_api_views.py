from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from lava.serializers.log_entry_serializer import (
    LogEntrySerializer
)
from lava.models.models import LogEntry
from lava.services import class_permissions as lava_permissions
from lava.utils import Result
from lava.messages import HTTP_403_MESSAGE


class LogEntryAPIViewSet(ReadOnlyModelViewSet):

    permission_classes = [lava_permissions.CanListLogEntry]
    serializer_class = LogEntrySerializer
    queryset = LogEntry.objects.none()

    def get_queryset(self):
        return LogEntry.filter(user=self.user, kwargs=self.request.GET)
    
    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, user=self.user, **kwargs)
        
    def list(self, request, *args, **kwargs):
        self.user = request.user
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        result = Result(False, HTTP_403_MESSAGE)
        return Response(result.to_dict(), status=status.HTTP_403_FORBIDDEN)
