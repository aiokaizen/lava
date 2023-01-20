import logging
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.contrib.admin.models import (
    LogEntry, DELETION, CHANGE, ADDITION
)
from django.contrib.admin.options import get_content_type_for_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from lava import settings as lava_settings
from lava.managers import DefaultBaseModelManager, TrashBaseModelManager
from lava.utils import (
    Result,
)


class BaseModel(models.Model):

    class Meta:
        verbose_name = "Base Model"
        verbose_name_plural = "Base Models"
        abstract = True
        ordering = ('-created_at', )
        default_permissions = ()
        # _class_name = label_lower.split('.')[1]
        _class_name = "object"
        permissions = (
            ('add_object', f"Can add {_class_name}"),
            ('change_object', f"Can update {_class_name}"),
            ('delete_object', f"Can delete {_class_name}"),
            ('soft_delete_object', f"Can soft delete {_class_name}"),
            ('view_object', f"Can view {_class_name}"),
            ('list_object', f"Can view {_class_name}"),
            ('restore_object', f"Can restore {_class_name}"),
        )

    created_at = models.DateTimeField(_("Created at"), null=True, blank=True, default=timezone.now)
    created_by = models.ForeignKey('lava.User', on_delete=models.PROTECT, null=True, blank=True)
    last_updated_at = models.DateTimeField(_("Last update"), null=True, blank=True, auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)

    objects = DefaultBaseModelManager()
    trash = TrashBaseModelManager()

    def create(self, user=None, m2m_fields=None):
        if self.id:
            return Result(False, _("This object is already created."))
        
        self.created_by = user

        self.save()

        if m2m_fields:
            for attr, value in m2m_fields:
                field = getattr(self, attr)
                field.set(value)

        if user:
            self.log_action(user, ADDITION, "Created")
            
        return Result(True, _("Object created successfully."))

    def update(self, user=None, update_fields=None, m2m_fields=None, message="Updated"):
        if not self.id:
            return Result(False, _("This object is not yet created."))
            
        if update_fields:
            self.save(update_fields=update_fields)
        else:
            self.save()

        if m2m_fields:
            for attr, value in m2m_fields:
                field = getattr(self, attr)
                field.set(value)

        if user:
            self.log_action(user, CHANGE, message)

        return Result(True, _("Object updated successfully."))

    def delete(self, user=None, soft_delete=True):

        success_message = _("The object was deleted successfully.")

        if soft_delete:
            self.deleted_at = timezone.now()
            self.update(user=user, update_fields=['deleted_at'], message="Soft Delete")
            return Result(True, success_message)

        if user:
            self.log_action(user, DELETION, "Deleted")

        super().delete()
        return Result(True, success_message)

    def duplicate(self, user=None):
        klass = self.__class__
        new = klass.objects.get(pk=self.pk)
        new.pk = None
        new._state.adding = True
        new.create(user=user)
        return Result(True, _("Object duplicated successfully."), instance=new)
    
    def restore(self, user=None):
        if not self.deleted_at:
            return Result(False, _("Object is not deleted!"))
            
        self.deleted_at = None
        result = self.update(user=user, update_fields=['deleted_at'], message="Restored")
        if result.is_error:
            return result
        return Result(True, _("The object has been restored successfully."))

    def log_action(self, user, action_flag, message):

        if not user:
            return
        
        LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=get_content_type_for_model(self).pk,
            object_id=self.pk,
            object_repr=self.__class__.__name__.upper(),
            action_flag=action_flag,
            change_message=message
        )

    @classmethod
    def get_filter_params(cls, user, kwargs=None):

        filter_params = Q()
        if kwargs is None:
            kwargs = {}

        if "created_by" in kwargs:
            filter_params &= Q(created_by=kwargs["created_by"])

        if "created_at" in kwargs:
            date = datetime.strptime(kwargs["created_at"], "%m-%d-%Y")
            filter_params &= Q(created_at__date=date)

        if "created_after" in kwargs:
            date = datetime.strptime(kwargs["created_after"], "%m-%d-%Y")
            filter_params &= Q(created_at__date__gte=date)

        if "created_before" in kwargs:
            date = datetime.strptime(kwargs["created_before"], "%m-%d-%Y")
            filter_params &= Q(created_at__date__lte=date)

        if "last_updated_at" in kwargs:
            date = datetime.strptime(kwargs["last_updated_at"], "%m-%d-%Y")
            filter_params &= Q(last_updated_at__date=date)

        if "last_updated_after" in kwargs:
            date = datetime.strptime(kwargs["last_updated_after"], "%m-%d-%Y")
            filter_params &= Q(last_updated_at__date__gte=date)

        if "last_updated_before" in kwargs:
            date = datetime.strptime(kwargs["last_updated_before"], "%m-%d-%Y")
            filter_params &= Q(last_updated_at__date__lte=date)

        if "deleted_at" in kwargs:
            date = datetime.strptime(kwargs["deleted_at"], "%m-%d-%Y")
            filter_params &= Q(deleted_at__date=date)

        if "deleted_after" in kwargs:
            date = datetime.strptime(kwargs["deleted_after"], "%m-%d-%Y")
            filter_params &= Q(deleted_at__date__gte=date)

        if "deleted_before" in kwargs:
            date = datetime.strptime(kwargs["deleted_before"], "%m-%d-%Y")
            filter_params &= Q(deleted_at__date__lte=date)

        return filter_params

    @classmethod
    def filter(cls, user=None, kwargs=None):
        filter_params = cls.get_filter_params(user, kwargs)
        queryset = cls.objects.filter(filter_params)
        return queryset
