import os
import logging
import threading
import itertools
from datetime import datetime, timedelta
from time import sleep
import zipfile

from django.apps import apps
from django.db import models
from django.db.models import Q
from django.core.files import File
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
    AbstractUser,
    Permission as BasePermissionModel,
    Group as BaseGroupModel
)
from django.contrib.admin.models import (
    LogEntry as BaseLogEntryModel,
    ADDITION, CHANGE, DELETION
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _, gettext
from django.utils import timezone

from easy_thumbnails.fields import ThumbnailerImageField

from lava import settings as lava_settings
from lava import validators as lava_validators
from lava.error_codes import REQUIRED_ERROR_CODE, UNIMPLEMENTED, UNKNOWN
from lava.messages import FORBIDDEN_MESSAGE, UNKNOWN_ERROR_MESSAGE, ACTION_NOT_ALLOWED
from lava.models.base_models import BaseModel, BaseModelMixin
from lava.utils import (
    Result,
    get_user_cover_filename,
    get_user_photo_filename,
    generate_password,
    strtobool,
    get_backup_file_filename,
    zipdir, zipf, dump_pgdb,
    generate_requirements,
    get_group_photo_filename
)
from lava.managers import (
    GroupManager, NotificationGroupManager, LavaUserManager,
    DefaultModelBaseManager
)
from lava.ws.services import send_ws_backup_status, send_ws_notification

try:
    from firebase_admin import messaging
except ImportError:
    messaging = None


class Preferences(models.Model):

    LIST_LAYOUT_CHOICES = (
        ("list", _("List")),
        ("cards", _("Cards")),
    )

    MENU_LAYOUT_CHOICES = (("default", _("Default")),)

    LANGUAGE_CHOICES = (
        ("en", _("English")),
        ("fr", _("Français")),
        ("es", _("Español")),
        ("ar", _("العربية")),
    )

    class Meta:
        verbose_name = _("Preferences")
        verbose_name_plural = _("Preferences")

    font_style = models.JSONField(_("Font style"), blank=True, default=dict)
    dark_theme = models.BooleanField(_("Dark theme on?"), default=False)
    list_layout = models.CharField(
        _("List layout"), max_length=8, choices=LIST_LAYOUT_CHOICES, default="list"
    )
    menu_layout = models.CharField(
        _("Menu layout"), max_length=16, choices=MENU_LAYOUT_CHOICES, default="default"
    )
    language = models.CharField(
        _("Language"), max_length=2, choices=LANGUAGE_CHOICES, default="en"
    )
    notifications_settings = models.JSONField(
        _("Notifications settings"),
        blank=True,
        default=dict,
        validators=[lava_validators.validate_notifications_settings],
    )

    def __str__(self):
        if hasattr(self, "user"):
            return f"{self.user} preferences"
        return super().__str__()


class LogEntry(BaseLogEntryModel):

    class Meta:
        verbose_name = _('Log entry')
        verbose_name_plural = _('Log entries')
        ordering = ['-action_time']
        default_permissions = ()
        permissions = (
            ('list_log_entry', _("Can view activity journal")),
            ('export_log_entry', _("Can export activity journal")),
        )

    @classmethod
    def get_filter_params(cls, kwargs=None):

        filters = Q()
        filter_params = Q()
        if kwargs is None:
            kwargs = {}

        if "user" in kwargs:
            filters |= Q(user=kwargs.get("user"))

        if "action_type" in kwargs:
            filters |= Q(action_flag=kwargs["action_type"])

        if "content_type" in kwargs:
            app_name, model = kwargs["content_type"].split('.')
            filters |= (
                Q(content_type__app_label=app_name) &
                Q(content_type__model=model)
            )

        if "action_time" in kwargs:
            date = datetime.strptime(kwargs["action_time"], "%m-%d-%Y")
            filter_params &= Q(action_time__date=date)

        if "created_after" in kwargs:
            date = datetime.strptime(kwargs["created_after"], "%m-%d-%Y")
            filter_params &= Q(action_time__date__gte=date)

        if "created_before" in kwargs:
            date = datetime.strptime(kwargs["created_before"], "%m-%d-%Y")
            filter_params &= Q(action_time__date__lte=date)

        return filter_params

    @classmethod
    def filter(cls, user=None, kwargs=None, include_admin_entries=False, trash=False):
        filter_params = cls.get_filter_params(kwargs)
        exclude_params = {}

        admin_users = User.objects.filter(username__in=['ekadmin', 'eksuperuser'])
        if user not in admin_users:
            exclude_params["user__in"] = admin_users

        base_queryset = cls.objects.none()
        if include_admin_entries:
            base_queryset = BaseLogEntryModel.objects.filter(filter_params).exclude(
                **exclude_params
            )

        queryset = cls.objects.filter(filter_params).exclude(
            **exclude_params
        )
        return queryset | base_queryset


class Permission(BaseModelMixin, BasePermissionModel):

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ['content_type__app_label', 'content_type__model', 'codename']
        proxy = True
        default_permissions = ()
        permissions = (
            ('set_permission', _("Can set permissions")),
        )

    def create(self, user=None, *args, **kwargs):

        return Result(False, _("You can not create a new permission."))

        result = super().create(user=user, *args, **kwargs)
        if result.is_error:
            return result
        return Result(True, _("The permission has been created successfully."), instance=self)

    def update(self, user=None, update_fields=None, *args, **kwargs):

        if len(update_fields or []) > 0:
            update_fields = ["name"]

        result = super().update(user=user, update_fields=update_fields, *args, **kwargs)
        if result.is_error:
            return result
        return Result(True, _("The permission has been updated successfully."))

    def delete(self, user=None, *args, **kwargs):

        return Result(False, _("You can not delete a permission."))

        result = super().delete(user=user, soft_delete=False)
        if result.is_error:
            return result
        return Result(True, _("The permission has been deleted successfully."))

    @classmethod
    def get_filter_params(cls, kwargs=None):
        filter_params = Q()

        if "name" in kwargs:
            filter_params |= Q(name__icontains=kwargs["name"])

        return filter_params

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = Permission.get_filter_params(kwargs)
        queryset = Permission.objects.filter(filter_params)

        return queryset


class Group(BaseModel, BaseGroupModel):

    class Meta(BaseModel.Meta):
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        default_permissions = ()

    description = models.TextField(_('Description'), blank=True)
    image = ThumbnailerImageField(
        _("Image"),
        upload_to=get_group_photo_filename,
        null=True, blank=True
    )
    parent = models.ForeignKey(
        'self', verbose_name=_("Parent"), on_delete=models.PROTECT,
        related_name="sub_groups", null=True, blank=True
    )
    notification_id = models.CharField(_("Notification group id"), max_length=256, blank=True)

    objects = GroupManager()
    all_objects = DefaultModelBaseManager()

    def create(self, user=None, m2m_fields=None):

        result = super().create(user=user, m2m_fields=m2m_fields)
        if result.is_error:
            return result

        return Result.success(_("Group has been created successfully."), instance=self)

    def update(self, user=None, update_fields=None, m2m_fields=None, message=""):

        result = super().update(
            user=user,
            update_fields=update_fields,
            m2m_fields=m2m_fields,
            message=message
        )
        if result.is_error:
            return result

        return Result.success(_("Group updated successfully."))

    def delete(self, user=None, **kwargs):
        result = super().delete(user=user, soft_delete=False)
        if result.is_error:
            return result

        return Result.success(_("The group has been deleted successfully."))

    def restore(self, user=None):
        return Result(False, "")

    @classmethod
    def get_filter_params(cls, kwargs=None):
        filter_params = Q()
        if kwargs is None:
            kwargs = {}

        if "name" in kwargs:
            filter_params |= Q(name__icontains=kwargs["name"])

        return filter_params

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = cls.get_filter_params(kwargs)
        queryset = super().filter(user=user, trash=trash, kwargs=kwargs)
        queryset = queryset.filter(filter_params)

        return queryset


class NotificationGroup(Group):

    class Meta:
        proxy = True

    objects = NotificationGroupManager()

    @classmethod
    def create_notification_groups(cls):
        for notification_id, group_data in lava_settings.NOTIFICATION_GROUPS_NAMES.items():
            group, _created = NotificationGroup.objects.get_or_create(
                notification_id=notification_id,
                name=group_data.get("name"),
                description=group_data.get("description", '')
            )
        return Result.success(_("All notification groups have been created successfully."))

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = cls.get_filter_params(kwargs)
        queryset = super().filter(user=user, trash=trash, kwargs=kwargs)
        queryset = queryset.filter(filter_params)

        return queryset


class User(BaseModel, AbstractUser):

    class Meta(AbstractUser.Meta):
        ordering = ("-date_joined", "last_name", "first_name")
        default_permissions = ()
        permissions = (
            ('change_current_user', _("Can change user profile")),
            ('delete_current_user', _("Can delete user profile")),
            ('soft_delete_current_user', _("Can soft delete user profile")),
        )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="users",
        related_query_name="user",
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="users",
        related_query_name="user",
    )

    photo = ThumbnailerImageField(
        _("Photo"), upload_to=get_user_photo_filename, blank=True, null=True
    )
    birth_day = models.DateField(_("Birth day"), blank=True, null=True)
    gender = models.CharField(
        _("Gender"),
        max_length=1,
        choices=lava_settings.GENDER_CHOICES,
        blank=True,
        default="",
    )
    full_name = models.CharField(_("Full name"), max_length=128, blank=True, default="")
    country = models.CharField(_("Country"), max_length=64, blank=True, default="")
    city = models.CharField(_("City"), max_length=64, blank=True, default="")
    street_address = models.TextField(_("Street address"), blank=True, default="")
    phone_number = models.CharField(
        _("Phone number"), max_length=32, blank=True, default=""
    )
    fax = models.CharField(_("Fax"), max_length=32, default="", blank=True)
    job = models.CharField(_("Job title"), max_length=64, blank=True, default="")
    cover_picture = ThumbnailerImageField(
        _("Cover picture"), upload_to=get_user_cover_filename, blank=True, null=True,
        help_text=_("Preferred image dimentions: (1200 x 250)")
    )
    preferences = models.OneToOneField(
        Preferences, on_delete=models.PROTECT, blank=True
    )
    tmp_pwd = models.CharField(
        _("Temporary password"), max_length=64, default="", blank=True
    )
    device_id_list = models.JSONField(
        _("Device IDs"),
        default=list,
        blank=True,
        help_text=_("A list of devices the the user is connected from."),
    )

    deleted_at = models.DateTimeField(_("Deleted at"), null=True)
    # is_email_valid = models.BooleanField(_("Email is valid"), default=False)

    objects = LavaUserManager()

    def get_choices_display(self):
        return f"{self.first_name} {self.last_name}"

    def groups_names(self):
        return self.groups.all().values_list("name", flat=True) if self.id else []

    def get_all_permissions(self):
        user_perms_ids = self.user_permissions.all().values_list("id", flat=True)
        groups_perms_ids = self.groups.all().values_list('permissions__id', flat=True)
        return Permission.objects.filter(pk__in=[*user_perms_ids, *groups_perms_ids])

    def create(
        self,
        user=None,
        photo=None,
        cover=None,
        groups=None,
        password=None,
        extra_attributes=None,
        create_associated_objects=True,
        force_is_active=False,
        generate_tmp_password=False,
        link_payments_app=True,
    ):

        if self.id:
            return Result(success=False, message=_("User is already created."), tag="warning")

        if not hasattr(self, "preferences"):
            self.preferences = Preferences.objects.create()

        if password is not None:
            result = self.validate_password(password)
            if not result.success:
                return result
        elif generate_tmp_password:
            password = generate_password(12)
            self.tmp_pwd = password

        if force_is_active:
            self.is_active = True
        elif settings.DJOSER["SEND_ACTIVATION_EMAIL"]:
            self.is_active = False

        self.full_name = f"{self.first_name + ' ' if self.first_name else ''}{self.last_name}"
        # We log the action manually on success
        result = super().create(user=None)
        if result.is_error:
            return result

        if password:
            self.set_password(password)

        update_fields = []
        if photo:
            self.photo = photo
            update_fields.append("photo")
        if cover:
            self.cover_picture = cover
            update_fields.append("cover_picture")
        if groups is not None:
            self.groups.set(groups)

        result = self.update(user=None, update_fields=update_fields)

        if link_payments_app:
            res = self.link_payments_app()
            if res.is_error:
                self.delete(soft_delete=False)
                return res
            # elif res.error_code == UNIMPLEMENTED:
            #     self.delete(soft_delete=False)
            #     raise Exception(res.to_dict())

        if groups and len(groups) == 1 and create_associated_objects:
            try:
                result = self.create_associated_objects(extra_attributes)
                if not result.success:
                    self.delete(soft_delete=False)
                    return result
            except Exception as e:
                self.delete(soft_delete=False)
                logging.error(e)
                return Result(success=False, message=UNKNOWN_ERROR_MESSAGE, error_code=UNKNOWN)

        if user:
            self.log_action(user, ADDITION)

        return Result(
            success=True,
            message=_("User has been created successfully."),
            instance=self
        )

    def link_payments_app(self):
        if "payments" not in settings.INSTALLED_APPS:
            return Result(False, _("Payments application is not installed"), tag="warning", error_code=UNIMPLEMENTED)

        res = self.create_account()
        if res.is_error:
            return res

        res = self.create_braintree_customer()
        if res.is_error:
            return res

        return Result(True, _("Payments application was implemented successfully."))

    def create_account(self):
        if "payments" not in settings.INSTALLED_APPS:
            return Result(False, _("Payments application is not installed"), tag="warning", error_code=UNIMPLEMENTED)
        if hasattr(self, "account"):
            return Result(False, _("Account already created"), tag="warning")

        from payments.models import Account

        account = Account(user=self)
        result = account.create()
        if result.is_error:
            return result
        self.account = account
        return Result(True, _("Associated account was created successfully."))

    def create_braintree_customer(self):
        if "payments" not in settings.INSTALLED_APPS:
            return Result(False, _("Payments application is not installed"), tag="warning", error_code=UNIMPLEMENTED)
        if hasattr(self, "customer"):
            return Result(False, _("Customer already created"), tag="warning")

        from payments.models import Customer

        bt_customer = Customer(user=self)
        try:
            result = bt_customer.create()
            if result.is_error:
                return result
            self.customer = bt_customer
            return Result(True, _("Associated BrainTree customer was created successfully."))
        except Exception as e:
            logging.error(e)
            return Result(False, _(
                    "Unable to connect to one of our servers, "
                    "please try again later. We apologize for the inconvenience."
                ),)

    def create_associated_objects(self, associated_object_attributes=None):
        model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
        groups = self.groups.all()
        associated_object_attributes = associated_object_attributes or {}
        if groups.count() != 1:
            return Result(
                success=False,
                message=_(
                    "This functionality is not valid for a user with many or no groups."
                ),
                tag="warning",
                error_code=UNIMPLEMENTED
            )
        group = groups.first()
        if group.name in model_mapping.keys():
            class_name = model_mapping[group.name]
            klass = apps.get_model(class_name)
            if "create" in dir(klass):
                obj = klass(user=self)
                result = obj.create(**associated_object_attributes)
                if not result.success:
                    return result
            else:
                obj = klass(user=self, **associated_object_attributes)
                obj.save()
        return Result(
            success=True, message=_("Associated object was created successfully.")
        )

    def update(self, user=None, update_fields=None, extra_attributes=None, message='', *args, **kwargs):
        groups = self.groups.all()
        if extra_attributes and groups.count() == 1:
            try:
                result = self.update_associated_objects(extra_attributes)
                if not result.success:
                    return result
            except Exception as e:
                return Result(success=False, message=str(e))

        if update_fields and ('first_name' in update_fields or 'last_name' in update_fields):
            self.full_name = f"{self.first_name + ' ' if self.first_name else ''}{self.last_name}"
            update_fields.append("full_name")

        result = super().update(user=user, update_fields=update_fields, message=message, *args, **kwargs)
        if result.is_error:
            return result

        return Result(success=True, message=_("User has been updated successfully."))

    def update_associated_objects(self, associated_object_attributes=None):
        model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
        groups = self.groups.all()
        associated_object_attributes = associated_object_attributes or {}
        if groups.count() != 1:
            return Result(
                success=False,
                tag="warning",
                message=_(
                    "This functionality is not valid for a user with many or no groups."
                ),
                error_code=UNIMPLEMENTED
            )

        group = groups.first()
        if group.name in model_mapping.keys():
            # Get class name (eg: `manager`) from class path (eg: myapp.Manager)
            class_name = model_mapping[group.name].split(".")[1].lower()
            obj = getattr(self, class_name, None)
            if obj is None:
                return Result(False, _("Invalid group type for this operation."))

            for key, value in associated_object_attributes.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            obj.save()
        return Result(
            success=True, message=_("Associated object was updated successfully.")
        )

    def delete(self, user=None, soft_delete=True):
        if not self.id:
            return Result(False, _("User is already deleted"), tag="warning")

        success_message = _("User has been deleted successfully")

        if soft_delete:
            # self.is_active = False
            self.deleted_at = timezone.now()
            self.update(user=user, update_fields=['deleted_at'], message="Soft Delete")
            return Result(success=True, message=success_message)

        # Unlink from payments app
        if hasattr(self, "customer"):
            self.customer.delete(delete_user=False)
        if hasattr(self, "account"):
            self.account.delete()

        preferences = self.preferences
        result = super().delete(user=user, soft_delete=soft_delete)
        if result.is_error:
            return result
        if preferences:
            preferences.delete()

        # Log the action
        if user:
            self.log_action(user, DELETION)

        return Result(success=True, message=success_message)

    def set_password(self, raw_password, user=None):
        self.password = make_password(raw_password)
        self._password = raw_password

        if not self.username:
            # We do this to fix an error where if the user is not found on login
            # Django calls User().set_password(rp) to increase request time span
            # for some reason?
            return super().set_password(raw_password)

        result = self.update(user=user, update_fields=["password"], message="Password Change")
        if result.is_error:
            return result
        return Result(True, _("Password has been changed successfully."))

    def restore(self, user=None):

        result = super().restore(user=user)
        if result.is_error:
            return result

        return Result(True, _("The user has been restored successfully."))

    def get_notifications(self):
        notifications = Notification.objects.filter(
            Q(target_users=self.id) | Q(target_groups__in=self.groups.all())
        )
        return notifications

    def get_unread_notifications(self):
        notifications = Notification.objects.filter(
            Q(target_users=self.id) | Q(target_groups__in=self.groups.all())
        ).exclude(seen_by__contains=self.id)
        return notifications

    def send_notification(
        self,
        title,
        content,
        category="alert",
        url="",
        target_users=None,
        target_groups=None,
        system_alert=False,
    ):

        sender = self if not system_alert else None

        notification = Notification(
            sender=sender, title=title, content=content, category=category, url=url
        )

        result = notification.create(
            m2m_fields=(('target_users', target_users), ('target_groups', target_groups))
        )
        if not result.success:
            return result

        # Send the notification by e-mail?

        # Send the notification via firebase api
        notification.send_firebase_notification()

        return Result(True, _("The notification was sent successfully."))

    def update_devices(self, device_id):
        if device_id not in self.device_id_list:
            self.device_id_list.append(device_id)
            self.save(update_fields=["device_id_list"])
        return Result(True)

    @classmethod
    def validate_password(cls, password):
        if not isinstance(password, str):
            return Result(success=False, message=_("`password` must be a string."))

        try:
            validate_password(password, User)
            return Result(success=True, message=_("User password is valid."))
        except ValidationError as e:
            return Result(
                success=False, message=_("Invalid password."), errors=e.messages
            )

    @classmethod
    def get_filter_params(cls, kwargs=None):

        filter_params = Q()

        if kwargs is None:
            kwargs = {}

        if "query" in kwargs:
            filter_params &= (
                Q(first_name__icontains=kwargs.get("query")) |
                Q(last_name__icontains=kwargs.get("query")) |
                Q(username__icontains=kwargs.get("query"))
            )

        if "first_name" in kwargs:
            filter_params &= Q(first_name__icontains=kwargs.get("first_name"))

        if "last_name" in kwargs:
            filter_params &= Q(last_name__icontains=kwargs.get("last_name"))

        if "is_active" in kwargs:
            filter_params &= Q(is_active=strtobool(kwargs["is_active"]))

        if "is_staff" in kwargs:
            filter_params &= Q(is_staff=strtobool(kwargs["is_staff"]))

        if "is_superuser" in kwargs:
            filter_params &= Q(is_superuser=strtobool(kwargs["is_superuser"]))

        return filter_params

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = User.get_filter_params(kwargs)

        base_queryset = super().filter(user=user, trash=trash, kwargs=kwargs)
        admin_users = User.objects.filter(username__in=["ekadmin", "eksuperuser"])

        if user and user not in admin_users:
            return base_queryset.exclude(pk__in=admin_users)

        return base_queryset.filter(filter_params)


class Notification(BaseModelMixin, models.Model):

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ("-date",)
        default_permissions = ()

    # empty sender means that the notification was generated by the system.
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    date = models.DateTimeField(_("Date sent"), auto_now_add=True)
    title = models.CharField(_("Title"), max_length=128)
    content = models.TextField(_("Content"), blank=True, default="")
    category = models.CharField(
        _("Category"),
        max_length=32,
        default="alert",
        choices=lava_settings.NOTIFICATION_CATEGORY_CHOICES,
    )
    url = models.CharField(
        _("URL"),
        help_text=_("Action URL"),
        default="",
        blank=True,
        max_length=200,
        validators=[lava_validators.SchemelessURLValidator()],
    )
    target_groups = models.ManyToManyField(
        Group, related_name="notifications", blank=True
    )
    target_users = models.ManyToManyField(
        User, related_name="notifications", blank=True
    )
    seen_by = models.JSONField(_("Seen by"), default=list, blank=True)

    def __str__(self):
        sender = self.sender if self.sender else "System"
        return f"{sender} : {self.title}"

    def seen(self, user):
        return user.id in self.seen_by

    def get_target_users(self):
        """Returns the sum of target users and the users in the target groups."""
        target_users = self.target_users.all()
        target_users_from_groups = User.objects.filter(
            groups__in=self.target_groups.all()
        )
        target_users = target_users | target_users_from_groups
        target_users = target_users.filter(is_active=True)
        return target_users

    def get_target_devices(self):
        target_users = self.get_target_users()
        devices_lists = list(target_users.values_list("device_id_list", flat=True))
        return list(itertools.chain(*devices_lists))

    def create(self, send_notification=True, **kwargs):
        can_create = False
        for field, value in kwargs.get('m2m_fields', ()):
            if field in ['target_users', 'target_groups'] and value:
                can_create = True
                break

        if not can_create:
            msg = _("You must specify either target users or target groups.")
            return Result.error(
                msg, errors={"target_users": [msg]}, error_code=REQUIRED_ERROR_CODE
            )

        result = super().create(**kwargs)
        if not result.is_success:
            return result

        if send_notification:
            send_ws_notification(self)
            self.send_firebase_notification()

        return Result(True, _("The notification has been created successfully."), instance=self)

    def mark_as_read(self, user):
        """Call this function when a user have seen the notification."""
        if user.id not in self.seen_by:
            self.seen_by.append(user.id)
            self.save(update_fields=['seen_by'])

    @classmethod
    def mark_as_read_bulk(cls, notifications, user):
        """
        Marks many notifications as read by the user.
        """
        for notification in notifications:
            notification.mark_as_read(user)

        return Result.success(_("The selected notifications have been marked as read."))

    def mark_as_not_read(self, user):
        """Call this function when a user marks the notification as not read."""
        if user.id in self.seen_by:
            self.seen_by.remove(user.id)
            self.save()

    def send_firebase_notification(self):
        """
        Send notification via firebase API.
        """
        if messaging is None:
            logging.warning("Firebase is not installed.")
            return Result.warning("Firebase is not installed.")
        if not lava_settings.FIREBASE_ACTIVATED:
            logging.warning("Firebase is not activated.")
            return Result.warning("Firebase is not activated.")

        registration_tokens = self.get_target_devices()
        data_object = None
        android_configs = messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                # click_action=self.url or None,
                priority="high",
            ),
        )
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=self.title, body=self.content),
            data=data_object,
            tokens=registration_tokens,
            android=android_configs,
        )

        # Send a message to the device corresponding to the provided
        # registration tokens.
        try:
            messaging.send_multicast(message)
        except Exception as e:
            logging.error(e)
            return Result(False, str(e))

        return Result(True)

    @classmethod
    def get_filter_params(cls, kwargs=None):

        filter_params = Q()

        if kwargs is None:
            kwargs = {}

        return filter_params

    @classmethod
    def filter(cls, user=None, kwargs=None):
        # filter_params = Notification.get_filter_params(kwargs)
        # return Notification.objects.filter(filter_params)
        return Notification.objects.all()


class Backup(BaseModel):

    class Meta(BaseModel.Meta):
        verbose_name = _("Backup")
        verbose_name_plural = _("Backups")

    name = models.CharField(_("Backup name"), max_length=256, blank=True)
    type = models.CharField(
        _("Backup type"), max_length=16, default="full_backup",
        choices=lava_settings.BACKUP_TYPE_CHOICES
    )
    status = models.CharField(
        _("Status"), max_length=16, default="running",
        choices=lava_settings.BACKUP_STATUS_CHOICES
    )
    backup_file = models.FileField(
        _("Backup file"), null=True, blank=True,
        upload_to=get_backup_file_filename
    )

    def __str__(self):
        return self.name

    def get_filename(self):
        return (
            f"{self.created_at.strftime('%Y%m%d%H%M%S')}_"
            f"{self.type}.zip"
        )

    def create(self, user=None, *args, **kwargs):
        return self.start_backup(user=user, *args, **kwargs)

    def update(self, *args, **kwargs):
        if 'message' not in kwargs:
            """ Allow modification for inner actions only (eg: soft_delete()). """
            return Result(False, ACTION_NOT_ALLOWED)
        return super().update(*args, **kwargs)

    def delete(self, user=None, soft_delete=True):
        backup_file = self.backup_file

        result = super().delete(user=user, soft_delete=soft_delete)
        if result.is_error:
            return result

        if backup_file:
            backup_file.delete()

        return Result(True, _("Backup has been deleted successfully."))

    def can_start_backup(self):

        if Backup.is_locked():
            return Result(False, _("A backup is already running, please wait "
                "until it's finished before starting a new one."), tag="warning")

        # min_period_between_backups = timedelta(hours=1)
        # daily_limit = 2
        # now = timezone.now()

        # all_backups = Backup.get_all_items()

        # latest_backup = all_backups.first()

        # if not latest_backup:
        #     return Result(True)

        # today_backups = all_backups.filter(created_at__date=now.date()).order_by("-created_at")

        # if today_backups.count() >= daily_limit:
        #     return Result(False, _("You can not create more than %d backups per day." % daily_limit))

        # latest_backup_time = latest_backup.created_at
        # if now < latest_backup_time + min_period_between_backups:
        #     return Result(False, _("You can only create one backup per hour"))

        return Result(True)

    def start_backup(self, user=None, *args, **kwargs):
        result = self.can_start_backup()
        if not result.success:
            return result

        self.name = (
            f"{self.created_at.strftime('%c')} "
            f"{self.get_type_display()}"
        )
        result = super().create(user, *args, **kwargs)
        if result.is_error:
            return result

        Backup.lock()

        backup = self
        threading.Thread(target=backup.run_backup, args=(user, )).start()

        return Result(True, _("Backup has been started, you will get notified once it is finished."))

    def run_backup(self, user=None):
        try:
            filename = get_backup_file_filename(self, "_")
            abs_filepath = os.path.join(settings.MEDIA_ROOT, filename)
            backup_dir = os.path.dirname(abs_filepath)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # This sleep was put here for testing purposes only.
            # Remove it once Backup interface is complete.
            sleep(10)

            if self.type == "db_backup":
                zipdir(settings.MEDIA_ROOT, abs_filepath, skip_dirs=['backup'])
            elif self.type == "full_backup":
                # Current Git branch             : git rev-parse --abbrev-ref HEAD
                # Current Git commit             : git rev-parse --verify HEAD
                # Current Git commit (Short hash): git rev-parse --short HEAD
                reqs_filename = generate_requirements()
                zipdir(settings.BASE_DIR, abs_filepath, skip_dirs=[
                    "venv", "tmp", "log", ".idea", "backup"
                ])
                os.remove(reqs_filename)

            ziph = zipfile.ZipFile(abs_filepath, 'a', zipfile.ZIP_DEFLATED)
            db_filename = dump_pgdb()
            zipf(db_filename, ziph=ziph)

            os.remove(db_filename)

            self.backup_file = filename
            self.status = "completed"
            self.save(update_fields=["status", "backup_file"])

            if user:
                notif = Notification(
                    title=gettext("Backup complete"),
                    content=gettext("A %(name)s that was started on %(date)s is finished successfully." % {
                        'name': self.get_type_display(), 'date': self.created_at.strftime("%c")
                    }),
                )
                target_groups = [NotificationGroup.objects.get(
                    notification_id=lava_settings.BACKUP_COMPLETED_NOTIFICATION_ID
                )]
                m2m_fields = [('target_users', [user]), ('target_groups', target_groups)]
                notif.create(m2m_fields=m2m_fields)

        except Exception as e:
            if user:
                notif = Notification(
                    title=gettext("Backup failed"),
                    content=gettext("A %s that was started on %s has failed.\nError: %s" % (
                        self.get_type_display(), self.created_at.strftime("%c"), e
                    )),
                )
                m2m_fields = [('target_users', [user])]
                notif.create(m2m_fields=m2m_fields)

            # Change status to failed
            self.status = "failed"
            self.save(update_fields=["status"])

        finally:
            send_ws_backup_status(self)
            Backup.unlock()

    def restore_backup(self, user=None):
        return Result.error("You can not restore a backup, this functionality is not implemented yet.")

    @classmethod
    def is_locked(cls):
        return os.path.exists(lava_settings.BACKUP_LOCK_TAG_PATH)

    @classmethod
    def lock(cls):
        open(lava_settings.BACKUP_LOCK_TAG_PATH, "w").close()

    @classmethod
    def unlock(cls):
        if Backup.is_locked():
            os.remove(lava_settings.BACKUP_LOCK_TAG_PATH)

    @classmethod
    def get_filter_params(cls, kwargs=None):

        filter_params = Q()

        if kwargs is None:
            kwargs = {}

        if "query" in kwargs or 'name' in kwargs:
            name = kwargs.get("query") or kwargs.get("name")
            filter_params &= Q(name__icontains=name)

        return filter_params

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = Backup.get_filter_params(kwargs)

        base_queryset = super().filter(user=user, trash=trash, kwargs=kwargs)

        return base_queryset.filter(filter_params)
