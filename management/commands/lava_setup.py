import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission

from lava.models import User, Group


class Command(BaseCommand):
    help = """
        This command should only be called once on the start of each
        project that includes lava app.
    """

    def handle(self, *args, **options):
        # Create the group 'ADMINS' if it does not exist
        try:
            group = Group.objects.get(name="ADMINS")
        except Group.DoesNotExist:
            group = Group(
                name='ADMINS',
                description="Admins have access to all available permissions in the system.",
                image=None
            )
            group.create()

        # Add all available permissions to group ADMINS
        group.permissions.add(*Permission.objects.all().values_list('id', flat=True))

        # Create the superadmin and the `ADMINS` group if they don't exist
        try:
            ekadmin = User.objects.get(username="ekadmin")
            logging.warning("superuser ekadmin already exists!")
        except User.DoesNotExist:
            ekadmin = User(
                username="ekadmin",
                email="admin@ekblocks.com",
                first_name="EKBlocks",
                last_name="Administrator",
                is_staff=True,
                is_superuser=True,
            )
            ekadmin.create(groups=[group], password="admin_pass", force_is_active=True, link_payments_app=False)
            logging.info("ekadmin was created successfully!")
