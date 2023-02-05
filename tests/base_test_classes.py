import os
import json
from copy import deepcopy

from django.conf import settings
from django.test import TestCase

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, URLPatternsTestCase

from lava.management.commands.lava_setup import Command as SetUpLava
from lava.management.commands.lava_install_demo import Command as LavaInstallDemo
from lava.models import User
from lava.utils import odict


class BaseTestMixin:

    _data = None
    demo_content_path = "lava/tests/content.json"

    @property
    def data(self):
        if self._data is None:
            with open(os.path.join(settings.BASE_DIR, self.demo_content_path), "r") as f:
                self._data = json.load(f)

        return deepcopy(self._data)


class BaseAPITest(APITestCase, URLPatternsTestCase, BaseTestMixin):

    users = None

    def authenticate_user(self, username):
        user = self.users[username]
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def setUp(self):
        print("\nStart setup...")
        super().setUp()
        SetUpLava().handle(no_logs=True)
        LavaInstallDemo().handle(num_users=3, suffix="testuser", skip_avatars=True, no_logs=True)

        self.users = odict(
            ekadmin=User.objects.get(username="ekadmin"),
            eksuperuser=User.objects.get(username="eksuperuser"),
            testuser_1=User.objects.get(username="testuser_1"),
            testuser_2=User.objects.get(username="testuser_2"),
            testuser_3=User.objects.get(username="testuser_3"),
        )

        for user in self.users.keys():
            Token.objects.create(user=self.users[user])

        self.authenticate_user(username="ekadmin")
        print("Setup complete.")


class BaseModelTest(TestCase, BaseTestMixin):

    users = None

    def setUp(self):
        print("\nStart setup...")
        super().setUp()
        SetUpLava().handle(no_logs=True)
        LavaInstallDemo().handle(num_users=2, suffix="testuser", skip_avatars=True, no_logs=True)
        self.users = odict(
            ekadmin=User.objects.get(username="ekadmin"),
            eksuperuser=User.objects.get(username="eksuperuser"),
            testuser_1=User.objects.get(username="testuser_1"),
            testuser_2=User.objects.get(username="testuser_2"),
        )

        for user in self.users.keys():
            Token.objects.create(user=self.users[user])

        print("Setup complete.")
