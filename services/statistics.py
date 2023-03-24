from django.contrib.sessions.models import Session
from django.db.models import Sum, Count, IntegerField
from django.db.models.fields.json import KeyTransform
from django.db.models.functions import Cast, Coalesce, TruncDate
from django.utils import timezone

from lava.models import *
from lava.serializers.backup_serializers import BackupSerializer
from lava.serializers.user_serializers import UserListSerializer
from lava.serializers.log_entry_serializer import LogEntrySerializer


def collect_statistics():

    # active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    connected_users = User.filter(kwargs={"is_active": "True"})[:7]
    users_count = User.filter().count()
    connected_users_serializer = UserListSerializer(connected_users, many=True)
    groups_count = Group.filter().count()
    backup_list = Backup.filter()
    backup_list_serializer = BackupSerializer(backup_list[:5], many=True)
    backups_count = backup_list.count()
    used_space = 34
    max_space = 128
    available_space_percent = round((used_space * 100) / max_space, 2)
    latest_actions = LogEntry.objects.all()[:7]
    latest_actions_serializer = LogEntrySerializer(latest_actions, many=True)

    statistics = {
        "users_count": users_count,
        "groups_count": groups_count,
        "backups_count": backups_count,
        "latest_backups": backup_list_serializer.data,
        "used_space": used_space,
        "max_space": max_space,
        "available_space_percent": available_space_percent,
        "active_users": connected_users_serializer.data,
        "latest_actions": latest_actions_serializer.data,
    }

    return statistics
