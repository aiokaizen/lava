from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from lava.models.models import LogEntry
from lava.serializers.base_serializers import ReadOnlyBaseModelSerializer
from lava.serializers.user_serializers import UserExerptSerializer


class LogEntrySerializer(ReadOnlyBaseModelSerializer):

    user = UserExerptSerializer()
    action_flag_display = serializers.CharField(source='get_action_flag_display')
    content_type = serializers.CharField(source='content_type.model')

    class Meta:
        model = LogEntry
        fields = [
            "id",
            "action_time",
            "user",
            "content_type",
            "object_id",
            "object_repr",
            "action_flag_display",
            "action_flag",
            "change_message",
        ]
        extra_kwargs = {
            "action_time": {"format": "%m/%d/%Y %H:%M:%S"},
        }
    