import json

from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from lava.models import Preferences, User, Group
from lava.utils import Result
from lava.views.api_views import (
    UserListCreate,
    UserRetrieveUpdateDestroy,
    change_password,
    maintenance,
)
from lava.views.main_views import home, activate_user, ResetPasswordConfirm


class TestAPIViews(TestCase):
    def setUp(self):
        """Runs before every test scenario"""
        self.client = APIClient()

        # Create users and groups
        self.create_groups()
        self.create_admin_user()
        self.create_test_users()

        # Authenticate
        result = self.authenticate(self.admin_user)
        if not result.success:
            raise Exception(result.message)

        # URLs
        self.user_list_url = reverse("user-list")
        self.user_detail_url = reverse("user-detail", args=[self.admin_user.pk])

    def create_groups(self):
        self.admin_groups = [Group.objects.create(name="ADMINS")]
        self.controller_groups = [Group.objects.create(name="CONTROLLERS")]
        self.organizer_groups = [Group.objects.create(name="ORGANIZERS")]
        self.participant_groups = [Group.objects.create(name="PARTICIPANTS")]

    def create_admin_user(self):
        self.admin_user = User(username="admin", is_superuser=True, is_staff=True)
        result = self.admin_user.create(
            force_is_active=True, generate_tmp_password=True, groups=self.admin_groups
        )
        if not result.success:
            raise Exception(result.message)

    def create_test_users(self):
        self.test_user1 = User(
            username="john",
            email="john@ekblocks.com",
            first_name="John",
            last_name="Doe",
        )
        self.test_user1.create(force_is_active=True, generate_tmp_password=True)
        self.test_user2 = User(
            username="anna",
            email="anna@ekblocks.com",
            first_name="Anna",
            last_name="Doe",
        )
        self.test_user2.create(force_is_active=True, generate_tmp_password=True)
        self.test_user3 = User(
            username="clark",
            email="clark@ekblocks.com",
            first_name="Clark",
            last_name="Doe",
        )
        self.test_user3.create(force_is_active=True, generate_tmp_password=True)
        self.test_user4 = User(
            username="albert",
            email="albert@ekblocks.com",
            first_name="Albert",
            last_name="Doe",
        )
        self.test_user4.create(force_is_active=True, generate_tmp_password=True)

    def authenticate(self, user):
        """Authenticates the user and populate self.headers."""
        authentication_url = reverse("login")
        credentials = {"username": user.username, "password": user.tmp_pwd}
        response = self.client.post(authentication_url, credentials, format="json")
        response_body = response.json()
        token = response_body.get("auth_token", None)
        if token is not None:
            self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
            return Result(True, "Authenticated!")
        return Result(False, response_body)

    def test_user_list_superuser(self):
        response = self.client.get(self.user_list_url)

        self.assertEquals(response.status_code, 200, response.json())

        results = response.json()["results"]
        self.assertEquals(len(results), 5)

    def test_user_list_normaluser(self):

        # Authenticate
        self.authenticate(self.test_user1)

        response = self.client.get(self.user_list_url)

        self.assertEquals(response.status_code, 200, response.json())

        results = response.json()["results"]
        self.assertEquals(len(results), 1)

    def test_signup_annonymous(self):
        photo = ""
        cover_picture = ""
        payload = {
            "username": "signup_user",
            "password": "admin_pass",
            "photo": photo,
            "first_name": "Jane",
            "last_name": "Doe",
            "birth_day": "03/17/1995",
            "gender": "M",
            "job": "Developper",
            "email": "k.mouad@ekblocks.com",
            "phone_number": "+212 688 991122",
            "country": "Morocco",
            "city": "Marrakech",
            "address": "325, 5th street, Marrakech",
            "cover_picture": cover_picture,
            "groups_names": ["ORGANIZERS"],
        }
        response = self.client.post(self.user_list_url, data=payload)

        self.assertEquals(response.status_code, 201, response.json())

        user = User.objects.get(username="signup_user")
        group = Group.objects.get(name="ORGANIZERS")
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.groups.all().count(), 1)
        self.assertEqual(user.groups.all().first(), group)
        self.assertEqual(user.tmp_pwd, "")

    # def test_user_retrieve_update_destroy_GET(self):
    #     response = self.client.get(self.user_detail_url)

    #     self.assertEquals(response.status_code, 200, response.json())

    # def test_user_retrieve_update_destroy_PATCH(self):
    #     response = self.client.get(self.user_detail_url)

    #     self.assertEquals(response.status_code, 200, response.json())

    # def test_user_retrieve_update_destroy_DELETE(self):
    #     response = self.client.get(self.user_detail_url)

    #     self.assertEquals(response.status_code, 200, response.json())


class TestMainViews(TestCase):
    def test_home_GET(self):
        client = APIClient()
        response = client.get(reverse("lava:home"))

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "lava/home.html")
