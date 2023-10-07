import time
import threading

import schedule

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.utils import ProgrammingError
from django.conf import settings


class LavaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lava"
    verbose_name = _("Administration")

    def ready(self):
        # This line initializes the signals module
        from lava import signals

        def start_schedule():
            while True:
                schedule.run_pending()
                time.sleep(5)

        try:
            from lava.models import BackupConfig

            BackupConfig.get_backup_config()

            from lava.settings import AUTOMATIC_BACKUP_ACTIVE

            automatic_backup_active = (
                True
                if (
                    (AUTOMATIC_BACKUP_ACTIVE is None and settings.DEBUG is False)
                    or AUTOMATIC_BACKUP_ACTIVE is True
                )
                else False
            )
            if automatic_backup_active:
                # Start the scheduling thread
                threading.Thread(target=start_schedule).start()

        except ProgrammingError:
            pass
