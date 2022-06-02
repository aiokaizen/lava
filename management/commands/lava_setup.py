import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = """
        This command should only be called once on the start of each
        project that includes lava app.
    """

    def handle(self, *args, **options):
        # Create the superadmin
        User = get_user_model()
        try:
            ekadmin = User.objects.get(username='ekadmin')
            logging.warning("ekadmin already exists!")
        except User.DoesNotExist:
            ekadmin = User.objects.create(username='ekadmin', is_staff=True, is_superuser=True)
            ekadmin.set_password('admin_pass')
            ekadmin.save()
            logging.info("ekadmin was created successfully!")
