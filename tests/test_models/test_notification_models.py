from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.models import CHANGE
from django.http import QueryDict

from lava.models.models import *
from lava.tests.base_test_classes import BaseModelTest


class UserModelTest(BaseModelTest):

    demo_content_path = "lava/tests/content.json"
    content_type = get_content_type_for_model(Notification)

    def get_notification_data(self, index=0):
        """set index to -1 to get all notifications."""
        notifications = self.data["notification"]
        if index == -1:
            return notifications
        return notifications[index]
