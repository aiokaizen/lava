import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission

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

        # Create the group 'ADMINS' if it does not exist
        group, _created = Group.objects.get_or_create(name="ADMINS")
        Group.objects.get_or_create(name="STANDARD")  # Default group for signed up users

        # Add all available permissions to group ADMINS
        group.permissions.add(*Permission.objects.all().values_list('id', flat=True))

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
            eksuperuser.create(groups=[group], password="admin_super_pass", force_is_active=True, link_payments_app=False)
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
            ekadmin.create(groups=[group], password="admin_pass", force_is_active=True, link_payments_app=False)
            logging.info("ekadmin was created successfully!")
