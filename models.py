import logging
import itertools

from django.apps import apps
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import AbstractUser, Group, Permission  # as BaseGroup,
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from firebase_admin import messaging

from lava import settings as lava_settings
from lava import validators as lava_validators
from lava.error_codes import UNIMPLEMENTED, UNKNOWN
from lava.messages import UNKNOWN_ERROR_MESSAGE
from lava.utils import (
    get_user_cover_filename,
    get_user_photo_filename,
    Result,
    generate_password,
)


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


# class Group(BaseGroup):
#     pass


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        ordering = ("-date_joined", "last_name", "first_name")

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
    address = models.TextField(_("Street address"), blank=True, default="")
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

    def groups_names(self):
        return self.groups.all().values_list("name", flat=True) if self.id else []

    def create(
        self,
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

        if photo or cover or groups:
            self.save()
            # FileInputs and ManyToMany fields must be saved after
            # the object has been already created
            self.photo = photo
            self.cover_picture = cover
            if groups is not None:
                self.groups.set(groups)

        if password is not None:
            result = self.validate_password(password)
            if not result.success:
                self.delete()
                return result
        elif generate_tmp_password:
            password = generate_password(12)
            self.tmp_pwd = password
        self.set_password(password)

        if force_is_active:
            self.is_active = True
        elif settings.DJOSER["SEND_ACTIVATION_EMAIL"]:
            self.is_active = False

        self.save()

        if link_payments_app:
            res = self.link_payments_app()
            if res.is_error:
                self.delete()
                return res
            elif res.error_code == UNIMPLEMENTED:
                self.delete()
                raise Exception(res.to_dict())

        # Refresh groups from db in case the groups param was not passed and the groups
        # attribute was already assigned before calling .create() method.
        groups = self.groups.all()
        if groups and groups.count() == 1 and create_associated_objects:
            try:
                result = self.create_associated_objects(extra_attributes)
                if not result.success:
                    self.delete()
                    return result
            except Exception as e:
                self.delete()
                logging.error(e)
                return Result(success=False, message=UNKNOWN_ERROR_MESSAGE, error_code=UNKNOWN)

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

    def update(self, update_fields=None, extra_attributes=None):
        groups = self.groups.all()
        if extra_attributes and groups and groups.count() == 1:
            try:
                result = self.update_associated_objects(extra_attributes)
                if not result.success:
                    return result
            except Exception as e:
                return Result(success=False, message=str(e))

        self.save(update_fields=update_fields)
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

    def delete(self, *args, **kwargs):
        if not self.id:
            return Result(False, _("User is already deleted"), tag="warning")

        # Unlink from payments app
        if hasattr(self, "customer"):
            self.customer.delete(delete_user=False)
        if hasattr(self, "account"):
            self.account.delete()

        preferences = self.preferences
        super().delete()
        if preferences:
            preferences.delete()
        return Result(success=True, message=_("User has been deleted successfully"))

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

    def create(self, target_users=None, target_groups=None):
        if not target_users and not target_groups:
            return Result(
                False, _("You must specify either target users or target groups.")
            )

        self.save()

        if target_users:
            self.target_users.set(target_users)

        if target_groups:
            self.target_groups.set(target_groups)

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
