import logging

from django.core.management.base import BaseCommand

from lava.models import User, Group


class Command(BaseCommand):
    help = """
        This command should only be called once on the start of each
        project that includes lava app.
    """

    def handle(self, *args, **options):
        # Create the superadmin and the `ADMINS` group if they don't exist
        try:
            ekadmin = User.objects.get(username="ekadmin")
            logging.warning("superuser ekadmin already exists!")
        except User.DoesNotExist:
            group, _ = Group.objects.get_or_create(name="ADMINS")
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
