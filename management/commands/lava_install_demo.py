import json
import os
import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

from lava.models import User, Group


class Command(BaseCommand):
    help = """
        This command adds some demo content to invoice app.
    """

    def handle(self, *args, **options):
        # Create some demo content here

        # Getting user data
        number_of_users = args.get('n', 25)

        # Creating groups
        groups = []
        groups_filename = os.path.join(
            settings.BASE_DIR, 'lava', 'demo_content', 'groups.json'
        )
        with open(groups_filename, 'r') as f:
            groups = json.load(f.read())
        
        for group in groups:
            try:
                Group.objects.create(
                    name=group['name']
                )
            except:
                pass

        # Creating users
        people = []
        people_filename = os.path.join(
            settings.BASE_DIR, 'lava', 'demo_content', 'people.json'
        )
        with open(people_filename, 'r') as f:
            people = json.load(f.read())

        for i in range(number_of_users):
            person = random.choice(people)
            people.remove(person)
            user = User.objects.create(
                username=f'emp{i}',
                first_name=person['first_name'],
                last_name=person['last_name'],
                email=person['email'],
                gender=person['gender'],
                photo=person['avatar'],
                country=person['country'],
                city=person['city'],
                address=person['address'],
                birth_day=person['birth_day'],
                job=person['job_title'],
            )
            user.set_password('user_pass')
            user.save(update_fields=['password'])
        