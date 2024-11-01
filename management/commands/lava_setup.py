import logging

from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from lava.models import User, Group, NotificationGroup
from lava import settings as lava_settings


class Command(BaseCommand):
    help = """
        This command should only be called once on the start of each
        project that includes lava app.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-logs",
            action="store_true",
            help="If this argument is set, the function will not print anything to the console.",
        )
        parser.add_argument(
            "--reset-perms",
            action="store_true",
            help="If this argument is set, all permissions will be removed and recreated (This action is irreversible!!).",
        )

    def handle(self, *args, **options):
        no_logs = options["no_logs"]
        reset_perms = options["reset_perms"]

        # Reset permissions:
        if reset_perms:
            logging.info("Resetting all permissions")
            Permission.objects.all().delete()
        # from django.utils import translation
        # translation.activate('fr')
        # print("current lang:", translation.get_language())

        # Create base model default permissions
        for model in apps.get_models():
            opts = model._meta
            content_type = ContentType.objects.get_for_model(model)

            model_full_name = f"{content_type.app_label}.{model.__name__.lower()}"
            if model_full_name in lava_settings.LOCKED_PERMISSIONS["models"]:
                print("skipping model permissions for:", model_full_name)
                continue

            if hasattr(model, "_create_default_permissions"):
                default_permissions = model._create_default_permissions()
                for code_name, verbose_name in default_permissions:

                    permission_name = f"{content_type.app_label}.{code_name}"
                    if (
                        permission_name
                        in lava_settings.LOCKED_PERMISSIONS["permissions"]
                    ):
                        print("Skipping permission:", permission_name)
                        continue

                    Permission.objects.get_or_create(
                        codename=code_name,
                        content_type=content_type,
                        defaults={
                            "name": verbose_name,
                        },
                    )
            else:
                # Create other models default permissions
                for perm in opts.default_permissions:
                    codename = f"{perm}_{opts.model_name}"
                    name = f"Can {perm} {opts.verbose_name}"

                    permission_name = f"{content_type.app_label}.{codename}"
                    if (
                        permission_name
                        in lava_settings.LOCKED_PERMISSIONS["permissions"]
                    ):
                        print("Skipping permission:", permission_name)
                        continue

                    Permission.objects.get_or_create(
                        codename=codename,
                        content_type=content_type,
                        defaults={"name": name},
                    )

            # Create other permissions (From Meta.permissions)
            for perm in opts.permissions:
                codename = perm[0]
                name = perm[1]

                permission_name = f"{content_type.app_label}.{codename}"
                if permission_name in lava_settings.LOCKED_PERMISSIONS["permissions"]:
                    print("Skipping permission:", permission_name)
                    continue

                Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults={"name": name},
                )

        # Create the group 'ADMINS' if it does not exist
        admins_group, _created = Group.objects.get_or_create(
            name="ADMINS", defaults={"is_system": True, "slug": "admins"}
        )
        # Group.objects.get_or_create(
        #     name="STANDARD", is_system=True
        # )  # Default group for signed up users

        # Add all available permissions to group ADMINS
        admins_group.permissions.add(
            *Permission.objects.all().values_list("id", flat=True)
        )

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
            eksuperuser.create(
                groups=[admins_group],
                password="admin_super_1234",
                force_is_active=True,
                link_payments_app=False,
            )
            logging.info("eksuperuser was created successfully!")

        try:
            ekadmin = User.objects.get(username="ekadmin")
            ekadmin.groups.add(admins_group)
            logging.warning("admin user ekadmin already exists!")
        except User.DoesNotExist:
            ekadmin = User(
                username="ekadmin",
                email="admin@ekblocks.com",
                first_name="EKBlocks",
                last_name="Administrator",
                is_staff=True,
            )
            ekadmin.create(
                groups=[admins_group],
                password="admin_1234",
                force_is_active=True,
                link_payments_app=False,
            )
            logging.info("ekadmin was created successfully!")
