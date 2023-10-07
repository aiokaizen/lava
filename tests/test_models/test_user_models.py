from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.models import CHANGE
from django.http import QueryDict

from lava.models.models import *
from lava.tests.base_test_classes import BaseModelTest


class UserModelTest(BaseModelTest):

    demo_content_path = "lava/tests/content.json"
    content_type = get_content_type_for_model(User)

    def get_user_data(self, index=0):
        """set index to -1 to get all users."""
        users = self.data["user"]
        if index == -1:
            return users
        return users[index]

    def test_create_user_succes_all_fileds_provided(self):
        """
        Ensure we can create a new user all fields are provided
        """
        data = self.get_user_data(1)
        del data["group_name"]
        del data["permission_name"]

        user = User(**data)
        result = user.create()
        self.assertTrue(result.is_success, result.message)

        user_count = User.objects.all().count()
        db_user = User.objects.first()
        self.assertEqual(user_count, 5)
        self.assertEqual(db_user.first_name, data["first_name"])
        self.assertEqual(db_user.last_name, data["last_name"])
        self.assertEqual(db_user.username, data["username"])
        self.assertEqual(db_user.email, data["email"])
        self.assertEqual(db_user.gender, data["gender"])

    def test_update_user_success(self):
        """
        Ensure we can update object user
        """
        data = self.get_user_data(1)
        del data["permission_name"]
        del data["group_name"]

        user = User(**data)
        result = user.create()
        self.assertTrue(result.success, result.message)

        changed_data = self.get_user_data(2)

        user.first_name = changed_data["first_name"]
        user.last_name = changed_data["last_name"]
        user.username = changed_data["username"]
        user.email = changed_data["email"]
        user.gender = changed_data["gender"]
        result = user.update(
            update_fields=["first_name", "last_name", "username", "email"]
        )
        self.assertTrue(result.is_success, result.message)

        user_updated = User.objects.all().first()
        self.assertTrue(user_updated.first_name, changed_data["first_name"])
        self.assertTrue(user_updated.last_name, changed_data["last_name"])
        self.assertTrue(user_updated.username, changed_data["username"])
        self.assertTrue(user_updated.email, changed_data["email"])
        self.assertTrue(user_updated.gender, changed_data["gender"])

    def test_delete_user_success(self):
        """
        Ensure we can delete a new objects
        """
        data = self.get_user_data(1)
        del data["permission_name"]
        del data["group_name"]

        user = User(**data)
        result = user.create()
        self.assertTrue(result.is_success, result.message)
        self.assertIsNotNone(User.objects.first())

        result = user.delete()
        self.assertTrue(result.is_success, result.message)

        self.assertIsNone(User.objects.filter(pk=user.id).first())
        self.assertIsNotNone(User.trash.filter(pk=user.id).first())

    def test_restore_user_success(self):
        """
        Ensure we can restore a new objects
        """
        data = self.get_user_data(1)
        del data["permission_name"]
        del data["group_name"]

        user = User(**data)
        result = user.create()
        self.assertTrue(result.is_success, result.message)
        self.assertIsNotNone(User.objects.first())

        result = user.delete()
        self.assertTrue(result.is_success, result.message)
        self.assertIsNone(User.objects.filter(pk=user.id).first())
        self.assertIsNotNone(User.trash.filter(pk=user.id).first())

        result = user.restore()
        self.assertTrue(result.is_success, result.message)
        self.assertIsNotNone(User.objects.filter(pk=user.id).first())
        self.assertIsNone(User.trash.filter(pk=user.id).first())

    def test_create_user_success_log(self):
        """
        Ensure we can log action of creation object user
        """
        data = self.get_user_data(2)
        del data["permission_name"]
        del data["group_name"]

        user = self.users["testuser_2"]

        user_created = User(**data)
        result = user_created.create(user=user)
        self.assertTrue(result.is_success, result.message)

        logs = LogEntry.objects.all()
        log = logs.first()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(log.user, user)
        self.assertEqual(log.content_type, self.content_type)
        self.assertEqual(log.action_flag, ADDITION)

    def test_update_user_success_log(self):
        """
        Ensure we can log the  action of update object user
        """
        data = self.get_user_data(1)
        del data["permission_name"]
        del data["group_name"]

        user = self.users["testuser_2"]

        user_updated = User(**data)
        result = user_updated.create()
        self.assertTrue(result.is_success, result.message)

        changed_data = self.get_user_data(2)

        user_updated.first_name = changed_data["first_name"]
        user_updated.last_name = changed_data["last_name"]
        result = user_updated.update(
            user=user, update_fields=["first_name", "last_name"]
        )
        self.assertTrue(result.is_success, result.message)

        logs = LogEntry.objects.all()
        log = logs.first()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(log.user, user)
        self.assertEqual(log.content_type, self.content_type)
        self.assertEqual(log.action_flag, CHANGE)

    def test_delete_user_success_log(self):
        """
        Ensure we can log the action of delete object user
        """
        data = self.get_user_data(1)
        del data["permission_data"]
        del data["group_data"]

        user = self.users["testuser_1"]
        user_deleted = User(**data)
        result = user_deleted.create()
        self.assertTrue(result.is_success, result.message)

        result = user_deleted.delete(user=user)
        self.assertTrue(result.is_success, result.message)

        logs = LogEntry.objects.all()
        log = logs.first()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(log.user, user)
        self.assertEqual(log.content_type, self.content_type)
        self.assertEqual(log.action_flag, CHANGE)
