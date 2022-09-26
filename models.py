from django.apps import apps
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import (
    AbstractUser,
    Group,  # as BaseGroup,
    Permission
)
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from lava import settings as lava_settings
from lava import validators as lava_validators
from lava.utils import (
    get_user_cover_filename, get_user_photo_filename,
    Result, generate_password
)


class Preferences(models.Model):

    LIST_LAYOUT_CHOICES = (
        ("list", _("List")),
        ("cards", _("Cards")),
    )

    MENU_LAYOUT_CHOICES = (
        ("default", _("Default")),
    )
    
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
    list_layout = models.CharField(_("List layout"), max_length=8, choices=LIST_LAYOUT_CHOICES, default="list")
    menu_layout = models.CharField(_("Menu layout"), max_length=16, choices=MENU_LAYOUT_CHOICES, default="default")
    language = models.CharField(_("Language"), max_length=2, choices=LANGUAGE_CHOICES, default="en")
    notifications_settings = models.JSONField(
        _("Notifications settings"),
        blank=True, default=dict,
        validators=[lava_validators.validate_notifications_settings]
    )

    def __str__(self):
        if hasattr(self, "user"):
            return f"{self.user} preferences"
        return super().__str__()


# class Group(BaseGroup):
#     pass


class User(AbstractUser):

    class Meta(AbstractUser.Meta):
        ordering = ('-date_joined', 'last_name', 'first_name')

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="users",
        related_query_name="user",
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="users",
        related_query_name="user",
    )

    photo = models.ImageField(_("Photo"), upload_to=get_user_photo_filename, blank=True, null=True)
    birth_day = models.DateField(_("Birth day"), blank=True, null=True)
    gender = models.CharField(_("Gender"), max_length=1, choices=lava_settings.GENDER_CHOICES, blank=True, default='')
    country = models.CharField(_("Country"), max_length=64, blank=True, default="")
    city = models.CharField(_("City"), max_length=64, blank=True, default="")
    address = models.TextField(_("Street address"), blank=True, default="")
    phone_number = models.CharField(_("Phone number"), max_length=32, blank=True, default="")
    fax = models.CharField(_("Fax"), max_length=32, default="", blank=True)
    job = models.CharField(_("Job title"), max_length=64, blank=True, default="")
    cover_picture = models.ImageField(_("Cover picture"), upload_to=get_user_cover_filename, blank=True, null=True)
    preferences = models.OneToOneField(Preferences, on_delete=models.PROTECT, blank=True)
    tmp_pwd = models.CharField(_("Temporary password"), max_length=64, default="", blank=True)

    # is_email_valid = models.BooleanField(_("Email is valid"), default=False)

    def groups_names(self):
        return self.groups.all().values_list('name', flat=True) if self.id else []
    
    def create(
        self, photo=None, cover=None, groups=None, password=None,
        extra_attributes=None, create_associated_objects=True,
        force_is_active=False, generate_tmp_password=False
    ):

        if self.id:
            return Result(
                success=False,
                message=_("User is already created.")
            )

        if not hasattr(self, 'preferences'):
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
                if self.id:
                    self.delete()
                return result
            self.set_password(password)
        elif generate_tmp_password:
            tmp_pwd = generate_password(12)
            self.tmp_pwd = tmp_pwd
            self.set_password(tmp_pwd)
        
        if force_is_active:
            self.is_active = True
        elif settings.DJOSER['SEND_ACTIVATION_EMAIL']:
            self.is_active = False

        self.save()

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
                return Result(success=False, message=str(e))

        return Result(
            success=True,
            message=_("User has been created successfully."),
        )
    
    def validate_password(self, password):
        if not isinstance(password, str):
            return Result(success=False, message=_("`password` must be a string."))

        try:
            validate_password(password, User)
            return Result(success=True, message=_("User password is valid."))
        except ValidationError as e:
            return Result(
                success=False, message=_("Invalid password."), errors=e.messages
            )
    
    def create_associated_objects(self, associated_object_attributes={}):
        model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
        groups = self.groups.all()
        associated_object_attributes = associated_object_attributes or {}
        if groups.count() != 1:
            return Result(
                success=False,
                tag='warning',
                message=_("This functionnality is not valid for a user with many or no groups."),
            )
        group = groups.first()
        if group.name in model_mapping.keys():
            class_name = model_mapping[group.name]
            klass = apps.get_model(class_name)
            if 'create' in dir(klass):
                object = klass(user=self)
                result = object.create(**associated_object_attributes)
                if not result.success:
                    return result
            else:
                object = klass(user=self, **associated_object_attributes)
                object.save()
        return Result(success=True, message=_("Accossiated object was created successfully."))
    
    def update(self, update_fields=None, extra_attributes=None):
        groups = self.groups.all()
        if groups and groups.count() == 1 and extra_attributes:
            try:
                result = self.update_associated_objects(extra_attributes)
                if not result.success:
                    return result
            except Exception as e:
                return Result(success=False, message=str(e))

        self.save(update_fields=update_fields)
        return Result(
            success=True,
            message=_("User has been updated successfully.")
        )
    
    def update_associated_objects(self, associated_object_attributes={}):
        model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
        groups = self.groups.all()
        associated_object_attributes = associated_object_attributes or {}
        if groups.count() != 1:
            return Result(
                success=False,
                tag='warning',
                message=_("This functionnality is not valid for a user with many or no groups."),
            )

        group = groups.first()
        if group.name in model_mapping.keys():
            # Get class name (eg: `manager`) from class path (eg: myapp.Manager)
            class_name = model_mapping[group.name].split('.')[1].lower()
            object = getattr(self, class_name, None)
            if object is None:
                return Result(False, _("Invalid group type for this operation."))
            
            for key, value in associated_object_attributes.items():
                if hasattr(object, key):
                    setattr(object, key, value)
            object.save()
        return Result(success=True, message=_("Accossiated object was updated successfully."))
    
    def delete(self):
        preferences = self.preferences
        if hasattr(self, 'customer'):
            self.customer.delete(delete_user=False)
        if hasattr(self, 'account'):
            self.account.delete()

        super().delete()
        if preferences:
            preferences.delete()
        return Result(
            success=True,
            message=_("User has been deleted successfully")
        )

    def get_notifications(self):
        notifications = Notification.objects.filter(
            Q(target_users=self.id) | Q(target_groups__in=self.groups.all())
        )
        return notifications
    
    def send_notification(self, title, content, category="alert", url="", target_users=None, target_groups=None, system_alert=False):

        sender = self if not system_alert else None

        notification = Notification(
            sender=sender,
            title=title,
            content=content,
            category=category,
            url=url
        )

        # Send the notification by e-mail?

        result = notification.create(
            target_users=target_users,
            target_groups=target_groups
        )
        if not result.success:
            return result
        
        return Result(True, _("The notification was sent successfully."))


class Notification(models.Model):

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ("-date", )
    
    # empty sender means that the notification was generated by the system.
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(_("Date sent"), auto_now_add=True)
    title = models.CharField(_("Title"), max_length=128)
    content = models.TextField(_("Content"), blank=True, default='')
    category = models.CharField(
        _("Category"), max_length=32, default='alert',
        choices=lava_settings.NOTIFICATION_CATEGORY_CHOICES
    )
    url = models.CharField(
        _("URL"), help_text=_("Action URL"), default="", blank=True,
        max_length=200,
        validators=[lava_validators.SchemelessURLValidator()]
    )
    target_groups = models.ManyToManyField(Group, related_name='notifications', blank=True)
    target_users = models.ManyToManyField(User, related_name='notifications', blank=True)
    seen_by = models.JSONField(_("Seen by"), default=list, blank=True)

    def __str__(self):
        sender = self.sender if self.sender else "System"
        return f"{sender} : {self.title}"
    
    def seen(self, user):
        return user.id in self.seen_by

    def create(self, target_users=None, target_groups=None):
        if not target_users and not target_groups:
            return Result(False, _("You must specify either target users or target groups."))
        
        self.save()

        if target_users:
            self.target_users.set(target_users)

        if target_groups:
            self.target_groups.set(target_groups)

        return Result(True, _("The notification has been created successfully."))
    
    def mark_as_read(self, user):
        """ Call this function when a user have seen the notification. """
        if user.id not in self.seen_by:
            self.seen_by.append(user.id)
            self.save()
    
    @classmethod
    def mark_as_read_bulk(self, notifications, user):
        """
        Marks many notifications as read by the user.
        """
        for notification in notifications:
            notification.mark_as_read(user)

    def mark_as_not_read(self, user):
        """ Call this function when a user marks the notification as not read. """
        if user.id in self.seen_by:
            self.seen_by.remove(user.id)
            self.save()
    
