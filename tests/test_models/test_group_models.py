from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.models import (CHANGE ,ADDITION)
from django.http import QueryDict

from lava.models.models import *
from lava.tests.base_test_classes import BaseModelTest


class GroupModelTest(BaseModelTest):

    demo_content_path =  "lava/tests/content.json"
    content_type = get_content_type_for_model(Group)

    def get_group_data(self, index=0):
        """ set index to -1 to get all permissions. """
        groups = self.data['group']
        if index == -1:
            return groups
        return groups[index]
    
    def test_create_group_success(self):
        """
        Ensure we can create a new object  group 
        """
        data = self.get_group_data(0)
        del data['parent']
        
        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_success, result.message)

        db_group = Group.objects.all().first()
        # group_counts = Group.objects.all().count()
        
        # self.assertEqual(group_counts, 1)
        self.assertEqual(db_group.name, data["name"])
        self.assertEqual(db_group.description, data["description"])
    
    def test_craete_group_error_prefix_of_notificated_group(self):
        """
        Ensure we can not create a new group objects with the prefix of notificated group
        """
        name = "#NOTIF_group_data"
        group = Group(name=name)
        result = group.create(notification_group=True)
        self.assertTrue(result.is_success, result.message)

        data = self.get_group_data(1)
        del data['parent']
        data['name'] = "#NOTIF_group_data"
        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_error, result.message)
    
    def test_update_group_success(self):
        """
        Ensure we can update object group 
        """
        data = self.get_group_data(0)
        del data['parent']
        
        change_data = self.get_group_data(1)
        del change_data['parent']

        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_success, result.message)
        
        group.name = change_data['name']
        group.description  = change_data['description']

        result = group.update(update_fields = ['name','description'])
        self.assertTrue(result.is_success, result.message)
        db_group = Group.objects.first()
        
        self.assertEqual(db_group.name, change_data["name"])
        self.assertEqual(db_group.description, change_data["description"])
    
    def test_update_group_error_prefix_of_notificated_group(self):
        """
        Ensure we can update object group 
        """
        name = "#NOTIF_group_data"
        group = Group(name=name)
        result = group.create(notification_group=True)
        self.assertTrue(result.is_success, result.message)

        data = self.get_group_data(0)
        del data['parent']
        
        change_data = self.get_group_data(1)
        del change_data['parent']
        change_data['name'] = "#NOTIF_group_data"

        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_success, result.message)
        
        group.name = change_data['name']
        group.description  = change_data['description']

        result = group.update(update_fields = ['name','description'])
        self.assertTrue(result.is_error, result.message)
        db_group = Group.objects.first()
        
        self.assertEqual(db_group.name, data["name"])
        self.assertEqual(db_group.description, data["description"])
    
    def test_create_group_success_log(self):
        """
        Ensure we can log action of created group object
        """
        data = self.get_group_data(0)
        del data['parent']
        group = Group(**data)
        
        user = self.users['testuser_2']
        result = group.create(user=user)
        self.assertTrue(result.is_success, result.message)
        
        logs = LogEntry.objects.all()
        log = logs.first()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(log.user, user)
        self.assertEqual(log.content_type, self.content_type)
        self.assertEqual(log.action_flag, ADDITION)
    
    def test_update_group_success_log(self):
        """
        Ensure we can log action of update group object
        """
        data = self.get_group_data(0)
        del data['parent']
        
        change_data = self.get_group_data(1)
        del change_data['parent']

        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_success, result.message)
        
        group.name = change_data['name']
        group.description  = change_data['description']

        user = self.users['testuser_2']
        result = group.update(user=user, update_fields=['name','description'])
        self.assertTrue(result.is_success, result.message)
        
        logs = LogEntry.objects.all()
        log = logs.first()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(log.user, user)
        self.assertEqual(log.content_type, self.content_type)
        self.assertEqual(log.action_flag, CHANGE)
    
    def test_delete_group_success(self):
        """
        Ensure we can delete group object
        """
        data = self.get_group_data(0)
        del data['parent']
        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_success, result.message)
        self.assertIsNotNone(Group.objects.first())

        result = group.delete()
        self.assertTrue(result.is_success, result.message)
        self.assertIsNone(Group.objects.filter(pk=group.id).first())
        
    def test_delete_group_error_with_prefix_in_notifacted_group(self):
        """
        Ensure we can not delete group thas start with prefix #NOTIF
        """
        data = self.get_group_data(0)
        del data['parent']
        data['name'] = "#NOTIF_group_data"

        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_success, result.message)
        
        result = group.delete()
        self.assertTrue(result.is_error, result.message)

    def test_delete_group_success_log(self):
        """
        Ensure we can delete group object
        """
        data = self.get_group_data(0)
        del data['parent']
        group = Group(**data)
        result = group.create()
        self.assertTrue(result.is_success, result.message)
        self.assertIsNotNone(Group.objects.first())

        user = self.users['testuser_2']
        result = group.delete(user=user)
        self.assertTrue(result.is_success, result.message)
        self.assertIsNone(Group.objects.filter(pk=group.id).first())
    
    def test_filter_group_succes(self):
        """
        Ensure we can filer groups with fields provided
        """
        data = self.get_group_data(0)
        del data['parent']
        data['name'] = 'Group 1'
        group1= Group(**data)
        result = group1.create()
        self.assertTrue(result.is_success, result.message)

        data2 = self.get_group_data(1)
        del data2['parent']
        data2['name'] = 'Group 2'
        group2 = Group(**data2)
        result = group2.create()
        self.assertTrue(result.is_success, result.message)

        filter_by_name = Group.filter(kwargs=QueryDict('name=Group 1'))
        self.assertEqual(filter_by_name.count(), 1)
        self.assertEqual(filter_by_name.first().name, "Group 1")
