import logging

from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from lava.models import User, Group, NotificationGroup


class Command(BaseCommand):
    help = """
        This command should only be called once on the start of each
        project that includes lava app.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-logs',
            action='store_true',
            help='If this argument is set, the function will not print anything to the console.',
        )

    def handle(self, *args, **options):

        no_logs = options["no_logs"]

        # # Reset permissions:
        # Permission.objects.all().delete()
        # from django.utils import translation
        # translation.activate('fr')
        # print("current lang:", translation.get_language())

        # Create base model default permissions
        models_count = 0
        perms_per_model = 0
        for model in apps.get_models():
            if hasattr(model, '_create_default_permissions'):
                default_permissions = model._create_default_permissions()
                models_count += 1
                if models_count == 1:
                    perms_per_model = len(default_permissions)
                for code_name, verbose_name in default_permissions:
                    content_type = ContentType.objects.get_for_model(model)
                    Permission.objects.get_or_create(
                        codename=code_name,
                        content_type=content_type,
                        defaults= {
                            'name': verbose_name,
                        }
                    )

        perms_count = Permission.objects.count()
        assert perms_count >= models_count * perms_per_model, (
            f"The number of permissions created ({perms_count}) is less than the minimum "
            f"enticipated number ({models_count * perms_per_model})"
        )

        # Create the group 'ADMINS' if it does not exist
        admins_group, _created = Group.objects.get_or_create(name="ADMINS")
        Group.objects.get_or_create(name="STANDARD")  # Default group for signed up users

        # Add all available permissions to group ADMINS
        admins_group.permissions.add(
            *Permission.objects.all().values_list('id', flat=True)
        )

        # Create notifications groups
        NotificationGroup.create_notification_groups()

        # Create the superuser and the ekadmin users if they don't exist
        try:
            eksuperuser = User.objects.get(username="eksuperuser")
            logging.warning("superuser eksuperuser already exists!")
        except User.DoesNotExist:
            eksuperuser = User(
                username="eksuperuser",
                email="admin@ekblocks.com",
                first_name="EKBlocks",
                last_name="SuperUser",
                is_staff=True,
                is_superuser=True,
            )
            eksuperuser.create(groups=[admins_group], password="admin_super_1234", force_is_active=True, link_payments_app=False)
            logging.info("eksuperuser was created successfully!")

        try:
            ekadmin = User.objects.get(username="ekadmin")
            logging.warning("admin user ekadmin already exists!")
        except User.DoesNotExist:
            ekadmin = User(
                username="ekadmin",
                email="admin@ekblocks.com",
                first_name="EKBlocks",
                last_name="Administrator",
                is_staff=True,
            )
            ekadmin.create(groups=[admins_group], password="admin_1234", force_is_active=True, link_payments_app=False)
            logging.info("ekadmin was created successfully!")
