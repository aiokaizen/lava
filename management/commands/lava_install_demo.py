import json
import mimetypes
import os
import random
import shutil
import requests
import wget
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from lava.models import User, Group
from lava.utils import get_user_photo_filename


class Command(BaseCommand):
    help = """
        This command adds some demo content to invoice app.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-num_users',
            nargs='?',
            default=25,
            type=int
        )

    def handle(self, *args, **options):
        # Create some demo content here

        # Getting user input
        number_of_users = options["num_users"]

        # Creating groups
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
            settings.TMP_ROOT, f'tmp_user_avatars_{today_str}'
        )
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        
        groups = Group.objects.all()

        for i in range(number_of_users):
            person = random.choice(people)
            people.remove(person)

            # Download avatar
            avatar = person["avatar"]
            filename = None
            if avatar:
                response = requests.get(avatar)
                if response.status_code == 200:
                    content_type = response.headers['content-type']
                    ext = mimetypes.guess_extension(content_type)
                    now_str = datetime.now().strftime("%H%M%S%f")
                    filename = os.path.join(download_path, f"{now_str}{ext}")
                    with open(filename, 'wb') as fp:
                        fp.write(response.content)

            user = User(
                username=f"user{i + 1}",
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
                groups=[random.choice(groups)],
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
            
        print(f'User {user.username} has been created.')
        
        shutil.rmtree(download_path, )
