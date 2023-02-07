import logging
import itertools
from datetime import datetime

from django.apps import apps
from django.db import models
from django.db.models import Q
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
from django.contrib.admin.options import get_content_type_for_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from lava import settings as lava_settings
from lava import validators as lava_validators
from lava.error_codes import UNIMPLEMENTED, UNKNOWN
from lava.messages import FORBIDDEN_MESSAGE, UNKNOWN_ERROR_MESSAGE
from lava.models.base_models import BaseModel, BaseModelMixin
from lava.services.permissions import (
    can_add_group, can_change_group, can_delete_group, can_list_group,
)
from lava.utils import (
    get_user_cover_filename,
    get_user_photo_filename,
    Result,
    generate_password,
    strtobool,
)
from lava.managers import (
    DefaultBaseModelManager, LavaUserManager
)

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
            ('list_logentry', f"Can view activity journal"),
            ('export_logentry', f"Can export activity journal"),
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
    def filter(cls, user=None, kwargs=None, include_admin_entries=False):
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


class Permission(BasePermissionModel, BaseModelMixin):

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ['content_type__app_label', 'content_type__model', 'codename']
        proxy = True
        default_permissions = ()
        permissions = (
            ('add_permission', "Can add permissions"),
            ('view_permission', "Can view permission details"),
            ('change_permission', "Can update permissions"),
            ('delete_permission', "Can delete permissions"),
            ('list_permission', "Can view permissions list"),
            ('set_permission', "Can set permissions"),
            ('export_permissions', "Can export permissions"),
        )

    def create(self, user=None):
        
        result = self.create(user=user)
        if result.is_error:
            return result
        return Result(True, _("The permission has been created successfully."))

    def update(self, user=None, update_fields=None):
        
        # TODO: Check if the deleted permission is defined in default_permissions
        # or permissions attributes of any registered model.
        
        result = self.update(user=user, update_fields=update_fields)
        if result.is_error:
            return result
        return Result(True, _("The permission has been updated successfully."))
    
    def delete(self, user=None):
        
        # TODO: Check if the deleted permission is defined in default_permissions
        # or permissions attributes of any registered model.
        
        result = super().delete(user=user, soft_delete=False)
        if result.is_error:
            return result
        return Result(True, _("The permission has been deleted successfully."))


class Group(BaseModelMixin, BaseGroupModel):

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        ordering = ("name", )
        proxy = True
        default_permissions = ()
        permissions = (
            ('add_group', "Can add group"),
            ('change_group', "Can update group"),
            ('delete_group', "Can delete group"),
            ('soft_delete_group', "Can soft delete group"),
            ('view_group', "Can view group"),
            ('list_group', "Can view group list"),
            ('view_trash_group', "Can view deleted groups"),
            ('restore_group', "Can restore group"),
        )

    # description = models.TextField(_('Description'), default='', blank=True)
    # image = models.ImageField(
    #     _("Image"),
    #     upload_to=get_group_photo_filename,
    #     null=True,
    #     blank=True
    # )
    # parent = models.ForeignKey(
    #     'self', verbose_name=_("Parent"), on_delete=models.PROTECT,
    #     related_name="sub_groups", null=True, blank=True
    # )
    trash = DefaultBaseModelManager()
    
    def create(self, user=None, m2m_fields=None):
        if user and not can_add_group(user):
            return Result(False, FORBIDDEN_MESSAGE)
        
        result = super().create(user=user, m2m_fields=m2m_fields)
        if result.is_error:
            return result
            
        return Result(True, _("Group created successfully."))
    
    def update(self, user=None, update_fields=None, m2m_fields=None, message=""):
        if user and not can_change_group(user):
            return Result(False, FORBIDDEN_MESSAGE)
        
        result = super().update(
            user=user,
            update_fields=update_fields,
            m2m_fields=m2m_fields,
            message=message
        )
        if result.is_error:
            return result

        return Result(True, _("Group updated successfully."))
    
    def delete(self, user=None):
        if user and not can_delete_group(user):
            return Result(False, FORBIDDEN_MESSAGE)

        result = super().delete(user=user, soft_delete=False)
        if result.is_error:
            return result

        return Result(True, _("The group has been deleted successfully."))
    
    def restore(self, user=None):
        return Result(False, "")
    
    @classmethod
    def get_filter_params(cls, user=None, kwargs=None):
        filter_params = Q()
        return filter_params
    
    @classmethod
    def filter(cls, user=None, kwargs=None):
        filter_params = cls.get_filter_params(user, kwargs)
        queryset = super().filter(user=user, kwargs=kwargs)
        queryset = queryset.filter(filter_params)
        if user and not can_list_group(user):
            return queryset.none()

        return queryset


class User(AbstractUser, BaseModel):

    class Meta(AbstractUser.Meta):
        ordering = ("-date_joined", "last_name", "first_name")
        default_permissions = ()
        permissions = (
            ('add_user', _("Can add user")),
            ('change_user', _("Can change user")),
            ('delete_user', _("Can delete user")),
            ('soft_delete_user', _("Can soft delete user")),
            ('view_user', _("Can view user")),
            ('list_user', _("Can view users list")),
            ('restore_user', _("Can restore user")),

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

    photo = models.ImageField(
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
    country = models.CharField(_("Country"), max_length=64, blank=True, default="")
    city = models.CharField(_("City"), max_length=64, blank=True, default="")
    street_address = models.TextField(_("Street address"), blank=True, default="")
    phone_number = models.CharField(
        _("Phone number"), max_length=32, blank=True, default=""
    )
    fax = models.CharField(_("Fax"), max_length=32, default="", blank=True)
    job = models.CharField(_("Job title"), max_length=64, blank=True, default="")
    cover_picture = models.ImageField(
        _("Cover picture"), upload_to=get_user_cover_filename, blank=True, null=True
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
        result = super().delete_alias(user=user, soft_delete=soft_delete)
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
            target_users=target_users, target_groups=target_groups
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
    def get_filter_params(cls, user=None, kwargs=None):

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
    def filter(cls, user=None, kwargs=None):
        filter_params = User.get_filter_params(user, kwargs)

        base_queryset = super().filter(user=user, kwargs=kwargs)
        admin_users = User.objects.filter(username__in=["ekadmin", "eksuperuser"])
        if user and user not in admin_users:
            return base_queryset.exclude(pk__in=admin_users)

        return base_queryset.filter(filter_params)


class Notification(models.Model):
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ("-date",)

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

    def create(self, target_users=None, target_groups=None, send_notification=False):
        if not target_users and not target_groups:
            return Result(
                False, _("You must specify either target users or target groups.")
            )

        self.save()

        if target_users:
            self.target_users.set(target_users)

        if target_groups:
            self.target_groups.set(target_groups)
        
        if send_notification:
            self.send_firebase_notification()

        return Result(True, _("The notification has been created successfully."))

    def mark_as_read(self, user):
        """Call this function when a user have seen the notification."""
        if user.id not in self.seen_by:
            self.seen_by.append(user.id)
            self.save()

    @classmethod
    def mark_as_read_bulk(cls, notifications, user):
        """
        Marks many notifications as read by the user.
        """
        for notification in notifications:
            notification.mark_as_read(user)

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
            return Result(False)
        if not lava_settings.FIREBASE_ACTIVATED:
            logging.warning("Firebase is not activated.")
            return Result(False)

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
