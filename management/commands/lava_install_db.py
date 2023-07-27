import os
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from lava.models import Bank


class Command(BaseCommand):
    help = """
        This command adds some demo content to invoice app.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-name',
            nargs='?',
            help="Database name. Choices: moroccan_banks, "
        )

    def handle(self, *args, **options):
        # Create some demo content here

        # Getting user input
        db_name = options["db_name"]

        if db_name in ["moroccan_banks", "moroccan_banks_extended"]:
            db_file_path = os.path.join(settings.BASE_DIR, f"lava/databases/{db_name}.json")
            with open(db_file_path) as f:
                bank_list = json.load(f)
                for bank_data in bank_list:
                    bank_data.pop("bank_id", None)
                    bank, created = Bank.get_or_create(
                        name=bank_data.pop("name"),
                        city=bank_data.pop("city", ""),
                        agency=bank_data.pop("agency", ""),
                        defaults=bank_data
                    )
                    if created:
                        print(f"Bank: {bank} has been created successfully.")
