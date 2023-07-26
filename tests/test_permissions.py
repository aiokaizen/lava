
from lava.tests.base_test_classes import BaseModelTest

from lava.enums import PermissionActionName
from lava.models import *
from lava.services.permissions import *


class PermissionsTest(BaseModelTest):

    def test_add_user_action_permission_exists(self):
        """
        Ensure we can not create a new category object when the name is not provided.
        """
        ekadmin = self.users.ekadmin
        action = PermissionActionName.Add
        has_perm = has_permission(ekadmin, User, action)

        self.assertEqual(has_perm, True)

    def test_add_user_action_permission_exists_denied(self):
        """
        Ensure we can not create a new category object when the name is not provided.
        """
        user1 = self.users.testuser_1
        action = PermissionActionName.Add
        has_perm = has_permission(user1, User, action)

        self.assertEqual(has_perm, False)

    def test_duplicate_user_str_permission_exists(self):
        """
        Ensure we can not create a new category object when the name is not provided.
        """
        ekadmin = self.users.ekadmin
        action = "duplicate_user"
        has_perm = has_permission(ekadmin, User, action)

        self.assertEqual(has_perm, True)

    def test_publish_user_str_permission_does_not_exist(self):
        """
        Ensure we can not create a new category object when the name is not provided.
        """
        ekadmin = self.users.ekadmin
        action = "publish_user"
        has_perm = has_permission(ekadmin, User, action)

        self.assertEqual(has_perm, False)
