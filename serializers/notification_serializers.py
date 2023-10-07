from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import empty

from lava.models import Notification
from lava.serializers.user_serializers import UserExerptSerializer
from lava.utils import humanize_datetime


class BulkNotificationActionSerializer(serializers.ModelSerializer):

    notifications_ids = serializers.ListField(
        label=_("Notifications ids"), required=True
    )

    class Meta:
        model = Notification
        fields = ["notifications_ids"]

    def __init__(self, user, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user

    def validate(self, attrs):
        validated_data = super().validate(attrs)


class NotificationSerializer(serializers.ModelSerializer):

    sender = UserExerptSerializer(required=False)
    seen = serializers.SerializerMethodField(label=_("Seen"))
    date = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "date",
            "title",
            "content",
            "category",
            "url",
            "target_groups",
            "target_users",
            "seen",
        ]
        read_only_fields = ["id", "sender", "date", "seen"]
        extra_kwargs = {
            "date": {
                "format": "%Y/%m/%d %H:%M:%S",
            },
            "writeonly_fields": [
                "target_groups",
                "target_users",
            ],
        }

    def __init__(self, user, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user

    def get_date(self, instance):
        return humanize_datetime(instance.date)

    def get_seen(self, instance):
        if not instance:
            return False
        return instance.seen(self.user)

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        target_groups = validated_data.get("target_groups")
        target_users = validated_data.get("target_users")
        if not target_groups and not target_users:
            raise serializers.ValidationError(
                _("You must specify either target groups or target users.")
            )
        return validated_data

    def create(self, validated_data):
        return self.user.send_notification(**validated_data)
