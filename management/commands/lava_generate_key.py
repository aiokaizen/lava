import os
import logging

from django.core.management.utils import get_random_secret_key
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = """
        This command generates a 128 long secret key and saves it to BASE_DIR/project_name_secret.key
        To change the key name, call the command using the parameter -name
        ex:
            python manage.py generate_key -name project_name
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-name',
            nargs='?',
            default='',
            type=str
        )

    def handle(self, *args, **options):

        name = options['name']
        if not name:
            name = os.path.basename(os.path.normpath(settings.BASE_DIR)).lower()

        path = os.path.join(settings.BASE_DIR, f"{name}_secret.key")
        
        secret = (
            f'{get_random_secret_key()}'
            f'{get_random_secret_key()}'
            f'{get_random_secret_key()}'
        )[:128]
        with open(path, 'w') as f:
            f.write(secret)
        
        logging.info(
            f"A key has been generated at {path}\n"
            f"Please copy it to /etc/secrets/[project_name]_secret_key.txt"
        )
