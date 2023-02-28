from django.apps import AppConfig


class LavaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lava"

    def ready(self):
        # This line initializes the signals module
        from lava import signals
