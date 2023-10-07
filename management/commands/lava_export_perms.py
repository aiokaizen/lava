import logging
import json
import os

from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.conf import settings

from lava.models import User, Group, NotificationGroup


class Command(BaseCommand):
    help = """
        This command should only be called once on the start of each
        project that includes lava app.
    """

    def handle(self, *args, **options):

        permissions_data = {}

        for model in apps.get_models():
            class_name = model.__name__.lower()
            permissions_data[class_name] = {}
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)
            for perm in permissions:
                if class_name not in perm.codename:
                    continue

                perm_id = perm.codename.split(f"_{class_name}")[0]
                codename = f"{content_type.app_label}.{class_name}.{perm.codename}"
                permissions_data[class_name][perm_id] = codename

        with open(os.path.join(settings.BASE_DIR, "permissions.json"), "w") as f:
            json.dump(permissions_data, f)
