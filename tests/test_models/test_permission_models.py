from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.models import CHANGE
from django.http import QueryDict

from lava.models.models import *
from lava.tests.base_test_classes import BaseModelTest


class PermissionModelTest(BaseModelTest):

    demo_content_path = "lava/tests/content.json"
    content_type = get_content_type_for_model(Permission)

    def get_permission_data(self, index=0):
        """set index to -1 to get all permissions."""
        permissions = self.data["permission"]
        if index == -1:
            return permissions
        return permissions[index]

    def test_create_permission_error(self):
        """
        Ensure we can not create a new object permissions
        """
        data = self.get_permission_data(1)
        del data["content_type"]

        permission = Permission(**data)
        result = permission.create()
        self.assertTrue(result.is_error, result.message)

    def test_update_permission_success(self):
        """
        Ensure we can update object permissions
        """
        # data = self.get_permission_data(1)

        permission = Permission.objects.get(id=100)
        permission.name = "Supprimer_Fournisseur"

        result = permission.update(update_fields=["name"])
        self.assertTrue(result.is_success, result.message)
        permission_db = Permission.objects.get(id=100)

        self.assertEqual(permission_db.name, "Supprimer_Fournisseur")

    def test_delete_permission_error(self):
        """
        Ensure we can not delete a new object permissions
        """
        data = self.get_permission_data(1)

        permission = Permission.objects.get(id=100)

        result = permission.delete()
        self.assertTrue(result.is_error, result.message)

    def test_update_permission_log_action(self):
        """
        Ensure we can log action of update permission objects
        """
        permission = Permission.objects.get(id=100)
        permission.name = "Supprimer_Fournisseur"

        user = self.users["testuser_2"]
        result = permission.update(user=user, update_fields=["name"])
        self.assertTrue(result.is_success, result.message)

        logs = LogEntry.objects.all()
        log = logs.first()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(log.user, user)
        self.assertEqual(log.content_type, self.content_type)
        self.assertEqual(log.action_flag, CHANGE)

    def test_filter_permission_succes(self):
        """
        Ensure we can filer permissions with fields provided
        """
        permission1 = Permission.objects.all()[100]
        permission2 = Permission.objects.all()[101]
        permission1.name = "Delete_supplier"
        permission2.name = "Change_supplier2"

        result = permission1.update(update_fields=["name"])
        self.assertTrue(result.is_success, result.message)

        result = permission2.update(update_fields=["name"])
        self.assertTrue(result.is_success, result.message)

        filter_by_name = Permission.filter(kwargs=QueryDict("name=Delete_supplier"))
        self.assertEqual(filter_by_name.count(), 1)
        self.assertEqual(filter_by_name.first().name, "Delete_supplier")
