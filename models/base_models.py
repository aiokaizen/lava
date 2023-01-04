import logging

from django.db import models
from django.contrib.admin.models import (
    LogEntry, DELETION, CHANGE, ADDITION
)
from django.contrib.admin.options import get_content_type_for_model
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from lava import settings as lava_settings
from lava.utils import (
    Result,
)


class BaseModel(models.Model):

    class Meta:
        verbose_name = "Base Model"
        verbose_name_plural = "Base Models"
        abstract = True

    created_at = models.DateTimeField(_("Created at"), null=True, blank=True, auto_now_add=True)
    created_by = models.OneToOneField(
        'lava.User', on_delete=models.PROTECT, related_name="participant"
    )
    last_updated_at = models.DateTimeField(_("Last update"), null=True, blank=True, auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)

    def create(self, user=None):
        if user:
            self.log_action(user, ADDITION, "Created")
        self.save()
        return Result(True, _("Object created successfully."))

    def update(self, user=None, update_fields=None, message=""):
        if update_fields:
            self.save(update_fields=update_fields)
        else:
            self.save()

        if user:
            self.log_action(user, CHANGE, message or "Updated")

        return Result(True, _("Object updated successfully."))

    def delete(self, user=None, soft_delete=False):

        success_message = _("Object deleted successfully.")

        if soft_delete:
            self.deleted_at = timezone.now()
            self.update(user=user, update_fields=['deleted_at'], message="Deleted")
            return Result(True, success_message)

        if user:
            self.log_action(user, DELETION, "Deleted")

        self.delete()
        return Result(True, success_message)

    def duplicate(self, user=None):
        klass = self.__class__
        new = klass.objects.get(pk=self.pk)
        new.pk = None
        new._state.adding = True
        new.create(user=user)
        return Result(True, _("Object duplicated successfully."), instance=new)

    def log_action(self, action_flag, message, user=None):

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

