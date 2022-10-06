from django.test import SimpleTestCase
from django.urls import reverse, resolve

from lava.views.api_views import (
    UserListCreate,
    UserRetrieveUpdateDestroy,
    change_password,
    maintenance,
)
from lava.views.main_views import home, activate_user, ResetPasswordConfirm


class TestUrls(SimpleTestCase):
    # We use SimpleTestCase any time we don't need to interact with the database

    def test_home_url(self):
        url = reverse("lava:home")
        self.assertEquals(resolve(url).func, home)

    def test_activate_user_url(self):
        url = reverse("lava:user-activate", args=["UID", "SOME_TOKEN"])
        self.assertEquals(resolve(url).func, activate_user)

    def test_reset_password_confirm_url(self):
        url = reverse("lava:user-reset-pwd-confirm", args=["UID", "SOME_TOKEN"])
        self.assertEquals(resolve(url).func.view_class, ResetPasswordConfirm)

    def test_user_list_create_url(self):
        url = reverse("lava:user-list")
        self.assertEquals(resolve(url).func.view_class, UserListCreate)

    def test_user_retrieve_update_destroy_url(self):
        url = reverse("lava:user-detail", args=[2])
        self.assertEquals(resolve(url).func.view_class, UserRetrieveUpdateDestroy)

    def test_change_password_url(self):
        url = reverse("lava:user-change-pwd", args=[2])
        self.assertEquals(resolve(url).func, change_password)

    def test_maintenance_url(self):
        url = reverse("lava:maintenance")
        self.assertEquals(resolve(url).func, maintenance)
