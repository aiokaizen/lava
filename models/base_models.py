import json
from datetime import datetime
import io
import os
import re

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
from django.urls import reverse

from lava.managers import DefaultModelBaseManager, DefaultModelTrashManager
from lava.enums import DeletePolicy
from lava.error_codes import NOT_CREATED_ERROR_CODE, REQUIRED_ERROR_CODE
from lava.utils import Result
from lava import settings as lava_settings


class BaseModelMixin:

    create_success_message = _("Object created successfully.")
    update_success_message = _("Object updated successfully.")
    delete_success_message = _("The object was deleted successfully.")
    duplicate_success_message = _("Object duplicated successfully.")
    restore_success_message = _("The object has been restored successfully.")
    default_delete_policy = DeletePolicy.SOFT_DELETE

    def get_url(self):
        try:
            return reverse(f'{self.__class__.__name__.lower()}-detail', args=[str(self.id)])
        except:
            return ""

    def get_absolute_url(self):
        return f"{lava_settings.HOST}{self.get_url()}"

    def create(self, user=None, m2m_fields=None, file_fields=None, clean=False):
        if self.pk:
            return Result(False, _("This object is already created."))

        # if clean:
        #     try:
        #         self.clean_fields()
        #     except ValidationError as e:
        #         return Result(False, _("Validation error."), errors=e.error_dict)

        self.created_by = user

        self.save()

        if m2m_fields:
            for attr, value in m2m_fields:
                field = getattr(self, attr)
                field.set(value)

        if file_fields:
            update_fields = []
            for attr, value in file_fields:
                if not value:
                    continue
                setattr(self, attr, value)
                update_fields.append(attr)

            if update_fields:
                self.save(update_fields=update_fields)

        if user:
            self.log_action(user, ADDITION)

        return Result(True, self.get_result_message('create'), instance=self)

    def update(self, user=None, update_fields=None, m2m_fields=None, message=""):
        if not self.pk:
            return Result(False, _("This object is not yet created."))

        # Get changed message before saving the object
        message = message or self.get_changed_message(m2m_fields, update_fields=update_fields)

        self.save(update_fields=update_fields)

        if m2m_fields:
            for attr, value in m2m_fields:
                field = getattr(self, attr)
                if not value:
                    field.clear()
                else:
                    field.set(value)

        if user:
            self.log_action(user, CHANGE, message)

        return Result.success(self.get_result_message('update'))

    def delete(self, user=None, soft_delete=None):

        if not self.id:
            return Result.error(
                _("This object is not yet created"),
                error_code=NOT_CREATED_ERROR_CODE
            )

        if getattr(self, 'deleted_at', None) and soft_delete:
            return Result.warning(
                _("This object is already deleted.")
            )

        if soft_delete is None:
            soft_delete = False
            if self.default_delete_policy == DeletePolicy.SOFT_DELETE:
                soft_delete = True

        if soft_delete:
            self.deleted_at = timezone.now()
            res = self.update(user=user, update_fields=['deleted_at'], message="Deletion")
            if res.is_error:
                return res
            return Result.success(self.get_result_message('delete'))

        if user:
            self.log_action(user, DELETION)

        super().delete()
        return Result.success(self.get_result_message('delete'))

    def duplicate(self, user=None, override_values=None):
        klass = self.__class__
        new = klass()
        override_values = override_values or {}

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

        return Result.success(self.get_result_message('duplicate'), instance=new)

    def restore(self, user=None):
        if not self.deleted_at:
            return Result(False, _("Object is not deleted!"))

        self.deleted_at = None
        result = self.update(user=user, update_fields=['deleted_at'], message="Restoration")
        if result.is_error:
            return result

        return Result.success(self.get_result_message('restore'))

    def get_changed_message(self, m2m_fields=None, update_fields=None):

        m2m_fields = m2m_fields or []

        changed_message = {"fields": {}}
        klass = self.__class__
        old_self = klass.get_all_items().get(pk=self.pk)
        m2m_fields_dict = {}
        for m2mfield in m2m_fields:
            m2m_fields_dict[m2mfield[0]] = m2mfield[1]

        for field in klass._meta.get_fields(include_parents=True):

            field_name = field.name
            if update_fields is not None and field_name not in update_fields:
                continue

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

    def get_result_message(self, action):
        message = getattr(self, f"{action}_success_message")
        str_message = str(message)

        fieldnames = re.findall(r'%\((\w+)\)\w', str_message)
        if fieldnames:
            format_dict = {}
            for fieldname in fieldnames:
                if hasattr(self, fieldname):
                    format_dict[fieldname] = getattr(self, fieldname, "")
            message = (message % format_dict)
        return message

    @classmethod
    def bulk_delete(cls, queryset, user=None, **kwargs):
        errors = {}
        soft_delete = not kwargs.get('trash', False)
        for obj in queryset:
            result = obj.delete(user, soft_delete=soft_delete)
            if result.is_error:
                errors[str(obj)] = result.message

        if errors:
            return Result.error(
                _("Some objects were not deleted."), errors=errors
            )

        return Result.success(_("%(count)s objects have been deleted successfully." % {
            'count': queryset.count()
        }))

    @classmethod
    def bulk_restore(cls, queryset, user=None, **kwargs):
        errors = {}
        for obj in queryset:
            result = obj.restore(user)
            if result.is_error:
                errors[str(obj)] = result.message

        if errors:
            return Result.error(
                _("Some objects were not restored."), errors=errors
            )

        return Result.success(_("%(count)s objects have been restored successfully." % {
            'count': queryset.count()
        }))

    @classmethod
    def get_object_or_none(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_or_create(cls, current_user=None, defaults=None, create_params=None, **kwargs):
        try:
            return cls.objects.get(**kwargs), False
        except cls.DoesNotExist:
            cleaned_kwargs = {}
            for key, value in kwargs.items():
                cleaned_kwargs[key.split("__")[0]] = value
            obj = cls(**cleaned_kwargs, **(defaults or {}))
            result = obj.create(current_user, **(create_params or {}))
            if result.is_success:
                return obj, True
            raise Exception(result.message)

    @classmethod
    def _create_default_permissions(cls):

        from django.utils.text import camel_case_to_spaces

        class_name = cls.__name__
        verbose_name = cls._meta.verbose_name
        verbose_name_plural = cls._meta.verbose_name_plural
        # Snake Case eg: GroupPermission > group_permission
        sc_class_name = class_name.lower()

        verbose_name = verbose_name or camel_case_to_spaces(class_name)
        verbose_name_plural = verbose_name_plural or f"{verbose_name}s"
        return (
            (f'list_{sc_class_name}', _("Can list %s" % (verbose_name_plural, ))),
            (f'list_all_{sc_class_name}', _("Can list all %s" % (verbose_name_plural, ))),
            (f'choices_{sc_class_name}', _("Can list choices %s" % (verbose_name_plural, ))),
            (f'add_{sc_class_name}', _("Can add %s" % (verbose_name, ))),
            (f'view_{sc_class_name}', _("Can view %s" % (verbose_name, ))),
            (f'view_excerpt_{sc_class_name}', _("Can view excerpt %s" % (verbose_name_plural, ))),
            (f'change_{sc_class_name}', _("Can update %s" % (verbose_name, ))),
            (f'duplicate_{sc_class_name}', _("Can duplicate %s" % (verbose_name, ))),
            (f'soft_delete_{sc_class_name}', _("Can soft delete %s" % (verbose_name, ))),
            (f'view_trash_{sc_class_name}', _("Can view deleted %s" % (verbose_name_plural, ))),
            (f'restore_{sc_class_name}', _("Can restore %s" % (verbose_name, ))),
            (f'delete_{sc_class_name}', _("Can delete %s" % (verbose_name, ))),
            (f'import_{sc_class_name}', _("Can import %s list" % (verbose_name_plural, ))),
            (f'export_{sc_class_name}', _("Can export %s list" % (verbose_name_plural, ))),
        )

    @classmethod
    def get_all_items(cls):
        return cls.objects.all() | cls.trash.all()

    @classmethod
    def get_filter_params(cls, kwargs=None):

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
        filter_params = BaseModelMixin.get_filter_params(kwargs)
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
        abstract = True
        ordering = ('-created_at', )
        default_permissions = ()

    created_at = models.DateTimeField(_("Created at"), null=True, blank=True, default=timezone.now)
    created_by = models.ForeignKey('lava.User', on_delete=models.PROTECT, null=True, blank=True)
    last_updated_at = models.DateTimeField(_("Last update"), null=True, blank=True, auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)

    objects = DefaultModelBaseManager()
    trash = DefaultModelTrashManager()
