from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LavaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lava"
    verbose_name = _("Administration")

    def ready(self):
        # This line initializes the signals module
        from lava import signals
