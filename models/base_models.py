import json
from datetime import datetime
import io
import os

from django.contrib.admin.models import (
    DELETION, CHANGE, ADDITION
)
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import (
    Q, ForeignKey, ManyToManyField, OneToOneField, FileField
)
from django.contrib.admin.options import get_content_type_for_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from lava.managers import DefaultBaseModelManager, TrashBaseModelManager
from lava.utils import Result
from lava.constants import DELETE_POLICY


class BaseModelMixin:

    create_success_message = _("Object created successfully.")
    update_success_message = _("Object updated successfully.")
    delete_success_message = _("The object was deleted successfully.")
    duplicate_success_message = _("Object duplicated successfully.")
    restore_success_message = _("The object has been restored successfully.")
    default_delete_policy = DELETE_POLICY.SOFT_DELETE

    def create(self, user=None, m2m_fields=None, file_fields=None, clean=False):
        if self.pk:
            return Result(False, _("This object is already created."))

        # if clean:
        #     try:
        #         self.clean_fields()
        #     except ValidationError as e:
        #         return Result(False, _("Erreurs de validation."), errors=e.error_dict)

        self.created_by = user

        self.save()

        if m2m_fields:
            for attr, value in m2m_fields:
                field = getattr(self, attr)
                field.set(value)

        if file_fields:
            update_fields = []
            for attr, value in file_fields:
                setattr(self, attr, value)
                update_fields.append(attr)
            self.save(update_fields=update_fields)


        if user:
            self.log_action(user, ADDITION)

        return Result(True, self.create_success_message, instance=self)

    def update(self, user=None, update_fields=None, m2m_fields=None, message=""):
        if not self.pk:
            return Result(False, _("This object is not yet created."))

        # Get changed message before saving the object
        message = message or self.get_changed_message(m2m_fields)

        self.save(update_fields=update_fields)

        if m2m_fields:
            for attr, value in m2m_fields:
                field = getattr(self, attr)
                field.set(value)

        if user:
            self.log_action(user, CHANGE, message)

        return Result.success(self.update_success_message)

    def delete(self, user=None, soft_delete=None):

        if soft_delete is None:
            soft_delete = False
            if self.default_delete_policy == DELETE_POLICY.SOFT_DELETE:
                soft_delete = True

        if soft_delete:
            self.deleted_at = timezone.now()
            res = self.update(user=user, update_fields=['deleted_at'], message="Deletion")
            if res.is_error:
                return res
            return Result.success(self.delete_success_message)

        if user:
            self.log_action(user, DELETION)

        super().delete()
        return Result.success(self.delete_success_message)

    def delete_alias(self, user=None, soft_delete=True):
        """
        This method is used in case of multi-inheritance, using super().delete()
        in that case may call models.Model.delete() instead.
        """
        return self.delete(user=user, soft_delete=soft_delete)

    def duplicate(self, user=None, override_values=dict):
        klass = self.__class__
        new = klass()

        ignore_fields = [
            'id',
            'created_at',
            'created_by',
            'last_updated_at',
            'deleted_at',
            *override_values.keys()
        ]
        file_fields = []
        m2m_fields = []
        opened_files = []

        for field in self._meta.fields:
            if field.name not in ignore_fields and not isinstance(field, OneToOneField):
                if isinstance(field, FileField):
                    filefield = getattr(self, field.name)
                    if filefield:
                        f = filefield.file.open(mode='rb')
                        opened_files.append(f)
                        stream = io.BytesIO(f.read())
                        io_file = File(ContentFile(stream.getvalue()))
                        io_file.name = f"file{os.path.splitext(filefield.name)[1]}"
                        file_fields.append((field.name, io_file))
                else:
                    setattr(new, field.name, getattr(self, field.name))

        for field in self._meta.many_to_many:
            m2m_fields.append((field.name, getattr(self, field.name).all()))

        for key, value in override_values.items():
            setattr(new, key, value)

        result = new.create(user=user, file_fields=file_fields, m2m_fields=m2m_fields)

        for f in opened_files:
            f.close()

        if result.is_error:
            return result

        return Result.success(self.duplicate_success_message, instance=new)

    def restore(self, user=None):
        if not self.deleted_at:
            return Result(False, _("Object is not deleted!"))

        self.deleted_at = None
        result = self.update(user=user, update_fields=['deleted_at'], message="Restoration")
        if result.is_error:
            return result

        return Result.success(self.restore_success_message)

    def get_changed_message(self, m2m_fields=None):

        if not m2m_fields:
            m2m_fields = []

        changed_message = {"fields": {}}
        klass = self.__class__
        old_self = klass.objects.get(pk=self.pk)
        m2m_fields_dict = {}
        for m2mfield in m2m_fields:
            m2m_fields_dict[m2mfield[0]] = m2mfield[1]

        for field in klass._meta.get_fields(include_parents=True):

            field_name = field.name
            old_value = getattr(old_self, field_name, None)
            new_value = getattr(self, field_name, None)

            if type(field) == ForeignKey:
                old_value = f"{old_value.id}|{old_value}" if old_value else None
                new_value = f"{new_value.id}|{new_value}" if new_value else None

            if type(field) == ManyToManyField and field_name in m2m_fields_dict:
                old_value = list(new_value.all().values_list("pk", flat=True))
                new_value = [item.pk for item in m2m_fields_dict[field_name]]

            if old_value != new_value:
                changed_message["fields"][field_name] = {
                    "old_value": str(old_value),
                    "new_value": str(new_value)
                }
        return json.dumps(changed_message, ensure_ascii=False)

    def log_action(self, user, action_flag, change_message=""):

        if not user:
            return

        from lava.models.models import LogEntry

        LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=get_content_type_for_model(self).pk,
            object_id=self.pk,
            object_repr=str(self),
            action_flag=action_flag,
            change_message=change_message
        )

    @classmethod
    def get_all_items(cls):
        return cls.objects.all() | cls.trash.all()

    @classmethod
    def get_filter_params(cls, user=None, kwargs=None):

        filter_params = Q()
        if kwargs is None:
            kwargs = {}

        if "created_by" in kwargs:
            try:
               created_by_id = int(kwargs["created_by"])
               filter_params &= Q(created_by=created_by_id)
            except ValueError:
                pass

        if "created_at" in kwargs:
            try:
                date = datetime.strptime(kwargs["created_at"], "%m-%d-%Y")
                filter_params &= Q(created_at__date=date)
            except ValueError:
                pass

        if "created_after" in kwargs:
            try:
                date = datetime.strptime(kwargs["created_after"], "%m-%d-%Y")
                filter_params &= Q(created_at__date__gte=date)
            except ValueError:
                pass

        if "created_before" in kwargs:
            try:
               date = datetime.strptime(kwargs["created_before"], "%m-%d-%Y")
               filter_params &= Q(created_at__date__lte=date)
            except ValueError:
                pass

        if "last_updated_at" in kwargs:
            try:
                date = datetime.strptime(kwargs["last_updated_at"], "%m-%d-%Y")
                filter_params &= Q(last_updated_at__date=date)
            except ValueError:
                pass

        if "last_updated_after" in kwargs:
            try:
                date = datetime.strptime(kwargs["last_updated_after"], "%m-%d-%Y")
                filter_params &= Q(last_updated_at__date__gte=date)
            except ValueError:
                pass

        if "last_updated_before" in kwargs:
            try:
                date = datetime.strptime(kwargs["last_updated_before"], "%m-%d-%Y")
                filter_params &= Q(last_updated_at__date__lte=date)
            except ValueError:
                pass

        if "deleted_at" in kwargs:
            try:
                date = datetime.strptime(kwargs["deleted_at"], "%m-%d-%Y")
                filter_params &= Q(deleted_at__date=date)
            except ValueError:
                pass

        if "deleted_after" in kwargs:
            try:
                date = datetime.strptime(kwargs["deleted_after"], "%m-%d-%Y")
                filter_params &= Q(deleted_at__date__gte=date)
            except ValueError:
                pass

        if "deleted_before" in kwargs:
            try:
                date = datetime.strptime(kwargs["deleted_before"], "%m-%d-%Y")
                filter_params &= Q(deleted_at__date__lte=date)
            except ValueError:
                pass

        return filter_params

    @classmethod
    def get_ordering_params(cls, kwargs):

        ordering = []
        if kwargs is None:
            kwargs = {}

        if "order_by" in kwargs:
            order_params = kwargs.getlist('order_by')
            object = cls()
            for param in order_params:
                param = param.lower()
                field_name = param if not param.startswith('-') else param[1:]
                if hasattr(object, field_name):
                    ordering.append(param)

        return ordering

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = BaseModelMixin.get_filter_params(user, kwargs)
        ordering = cls.get_ordering_params(kwargs)
        if not trash:
            queryset = cls.objects.filter(filter_params)
        else:
            queryset = cls.trash.filter(filter_params)
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset


class BaseModel(BaseModelMixin, models.Model):

    class Meta:
        verbose_name = "Base Model"
        verbose_name_plural = "Base Models"
        abstract = True
        ordering = ('-created_at', )
        default_permissions = ()
        # _class_name = label_lower.split('.')[1]
        _class_name = "object"
        permissions = (
            ('add_object', _("Can add %s" % (_class_name, ))),
            ('change_object', _("Can update %s" % (_class_name, ))),
            ('delete_object', _("Can delete %s" % (_class_name, ))),
            ('soft_delete_object', _("Can soft delete %s" % (_class_name, ))),
            ('view_object', _("Can view %s" % (_class_name, ))),
            ('list_object', _("Can list %s" % (_class_name, ))),
            ('restore_object', _("Can restore %s" % (_class_name, ))),
        )

    created_at = models.DateTimeField(_("Created at"), null=True, blank=True, default=timezone.now)
    created_by = models.ForeignKey('lava.User', on_delete=models.PROTECT, null=True, blank=True)
    last_updated_at = models.DateTimeField(_("Last update"), null=True, blank=True, auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)

    objects = DefaultBaseModelManager()
    trash = TrashBaseModelManager()
