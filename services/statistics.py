from django.contrib.sessions.models import Session
from django.db.models import Sum, Count, IntegerField
from django.db.models.fields.json import KeyTransform
from django.db.models.functions import Cast, Coalesce, TruncDate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from lava.models import *
from lava.serializers.backup_serializers import BackupSerializer
from lava.serializers.user_serializers import UserListSerializer
from lava.serializers.log_entry_serializer import LogEntrySerializer


def collect_statistics(user=None):

    # active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    connected_users = User.filter(user=user, params={"is_active": "True"})[:7]
    users_count = User.filter(user=user).count()
    connected_users_serializer = UserListSerializer(connected_users, many=True)
    groups_count = Group.filter(user=user).count()
    backup_list = Backup.filter(user=user)
    backup_list_serializer = BackupSerializer(backup_list[:5], many=True)
    backups_count = backup_list.count()
    used_space = 34
    max_space = 128
    available_space_percent = round((used_space * 100) / max_space, 2)
    latest_actions = LogEntry.filter(user=user)[:7]
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


def get_daily_actions(user=None):

    daily_actions = (
        LogEntry.filter(user=user)
        .order_by("-action_time")
        .annotate(action_day=TruncDate("action_time"))
        .values("action_day")
        .annotate(
            count=Count("id"),
        )
    )[:30]

    actions_data = {
        "actions": dict(),
    }

    for action_data in daily_actions:
        action_day = action_data["action_day"].strftime("%Y-%m-%d")

        if action_day not in list(actions_data["actions"].keys()):
            actions_data["actions"][action_day] = [action_day, 0]

        actions_data["actions"][action_day][1] += action_data["count"]

    actions_data["actions"] = list(actions_data["actions"].values())

    return actions_data


def get_indicators(user=None):

    users_count = User.filter(user=user).count()
    groups_count = Group.filter(user=user).count()
    backup_list = Backup.filter(user=user)
    backups_count = backup_list.count()

    statistics = [
        {
            "title": _("Utilisateurs"),
            "value": users_count,
            "status": None,
            "subtitle": _("Total des utilisateurs"),
        },
        {
            "title": _("Groupes"),
            "value": groups_count,
            "status": None,
            "subtitle": _("Total des groupes"),
        },
        {
            "title": _("Sauvegardes"),
            "value": backups_count,
            "status": None,
            "subtitle": _("Total des sauvegardes"),
        },
    ]
    return statistics


def get_spaces(user=None):

    used_space = 34
    max_space = 128
    available_space_percent = round((used_space * 100) / max_space, 2)

    statistics = {
        "used_space": used_space,
        "max_space": max_space,
        "available_space_percent": available_space_percent,
    }
    return statistics


def get_active_users(user=None):

    connected_users = User.filter(user=user, params={"is_active": "True"})[:7]

    connected_users_serializer = UserListSerializer(connected_users, many=True)

    return connected_users_serializer.data


def get_latest_actions(user=None):

    latest_actions = LogEntry.filter(user=user)[:7]

    latest_actions_serializer = LogEntrySerializer(latest_actions, many=True)

    return latest_actions_serializer.data
