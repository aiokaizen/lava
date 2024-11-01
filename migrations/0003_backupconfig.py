# Generated by Django 3.2 on 2023-10-01 14:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import lava.models.base_models


class Migration(migrations.Migration):

    dependencies = [
        ("lava", "0002_auto_20230927_1559"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        blank=True,
                        default=django.utils.timezone.now,
                        null=True,
                        verbose_name="Created at",
                    ),
                ),
                (
                    "last_updated_at",
                    models.DateTimeField(
                        auto_now=True, null=True, verbose_name="Last update"
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                (
                    "automatic_backup_hour_interval",
                    models.PositiveIntegerField(
                        default=168,
                        help_text="The number of hours between automatic backups.",
                        verbose_name="Automatic backup interval",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Backup Configuration",
                "verbose_name_plural": "Backup Configuration",
            },
            bases=(lava.models.base_models.BaseModelMixin, models.Model),
        ),
    ]