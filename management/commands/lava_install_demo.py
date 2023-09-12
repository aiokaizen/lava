import json
import mimetypes
import os
import random
import shutil
import requests
import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from lava.models import User, Group
from lava.utils import get_user_photo_filename, slugify
from lava import settings as lava_settings


class Command(BaseCommand):
    help = """
        This command adds some demo content to invoice app.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-num-users',
            nargs='?',
            default=25,
            type=int,
            help="Number of users to create, defaults to 25."
        )
        parser.add_argument(
            '--skip-avatars',
            action='store_true',
            help='If this argument is set, the users will be created without profile pictures.',
        )
        parser.add_argument(
            '-suffix',
            nargs='?',
            default='user',
            type=str,
            help="The username suffix, defaults to user. eg: user1, user2, ..."
        )
        parser.add_argument(
            '-s',
            '--skip-groups',
            action='store_true',
            default=False,
            help='If this argument is set, groups will not be created.',
        )
        parser.add_argument(
            '--no-logs',
            action='store_true',
            help='If this argument is set, the function will not print anything to the console.',
        )

    def handle(self, *args, **options):
        # Create some demo content here

        # Getting user input
        number_of_users = options["num_users"]
        skip_avatars = options["skip_avatars"]
        username_suffix = options["suffix"]
        no_logs = options["no_logs"]
        skip_groups = options["skip_groups"]

        logging.info(
            "Start importing demo content with the following parameters:\n"
            f"\t-num_users={number_of_users}\n"
            f"\t-skip_avatars={skip_avatars}\n"
            f"\t-suffix={username_suffix}\n"
        )

        # Creating groups
        if not skip_groups:
            groups = []
            groups_filename = os.path.join(
                settings.BASE_DIR, "lava", "demo_content", "groups.json"
            )
            with open(groups_filename, "r") as f:
                data = f.read()
                groups = json.loads(data)

                for group in groups:
                    Group.objects.get_or_create(name=group["name"])

        # Creating users
        people = []
        people_filename = os.path.join(
            settings.BASE_DIR, "lava", "demo_content", "people.json"
        )
        with open(people_filename, "r") as f:
            data = f.read()
            people = json.loads(data)

        today_str = datetime.now().strftime("%Y%m%d")
        download_path = os.path.join(
            lava_settings.TMP_ROOT, f'tmp_user_avatars_{today_str}'
        )
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        groups = Group.objects.all()
        user_avatar = "https://i.pravatar.cc/150"

        groups_indexes = {}

        for i in range(number_of_users):
            person = random.choice(people)
            people.remove(person)

            # Download avatar
            filename = None
            if not skip_avatars:
                response = requests.get(user_avatar)
                if response.status_code == 200:
                    content_type = response.headers['content-type']
                    ext = mimetypes.guess_extension(content_type)
                    now_str = datetime.now().strftime("%H%M%S%f")
                    filename = os.path.join(download_path, f"{now_str}{ext}")
                    with open(filename, 'wb') as fp:
                        fp.write(response.content)

            username = f"{username_suffix}_{i + 1}"
            user_group = random.choice(groups)
            groups_indexes[user_group.id] = groups_indexes.get(user_group.id, 0) + 1
            if username_suffix == "user":
                user_index = groups_indexes[user_group.id]
                username = f"{slugify(user_group.name)}_{user_index}"

            user = User(
                username=username,
                first_name=person["first_name"],
                last_name=person["last_name"],
                email=person["email"],
                gender=person["gender"],
                country=person["country"],
                city=person["city"],
                street_address=person["address"],
                birth_day=person["birth_day"],
                job=person["job_title"],
            )
            user.create(
                groups=[user_group],
                password="admin_pass",
                force_is_active=True,
                link_payments_app=False
            )
            if filename:
                with open(filename, 'rb') as f:
                    user.photo.save(
                        get_user_photo_filename(user, filename),
                        File(f)
                    )
                    user.update(update_fields=['photo'])

            if not no_logs:
                print(f'User {user.username} has been created.')

        shutil.rmtree(download_path, )
