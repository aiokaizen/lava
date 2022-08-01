from django.apps import apps
from django.db import models
from django.contrib.auth import get_user
from django.conf import settings
from django.contrib.auth.models import (
    AbstractUser,
    Group,  # as BaseGroup,
    Permission
)
from django.utils.translation import ugettext_lazy as _

from lava import settings as lava_settings
from lava.utils import (
    get_user_cover_filename, get_user_photo_filename,
    Result
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
    address = models.TextField(_("Address"), blank=True, default="")
    phone_number = models.CharField(_("Phone number"), max_length=32, blank=True, default="")
    fax = models.CharField(_("Fax"), max_length=32, default="", blank=True)
    job = models.CharField(_("Job title"), max_length=64, blank=True, default="")
    cover_picture = models.ImageField(_("Cover picture"), upload_to=get_user_cover_filename, blank=True, null=True)
    preferences = models.OneToOneField(Preferences, on_delete=models.PROTECT, blank=True)

    def groups_names(self):
        return self.groups.all().values_list('name', flat=True)
    
    def create(self, photo=None, cover=None, groups=None, extra_attributes=None):

        if self.id:
            return Result(
                success=False,
                message=_("User is already saved.")
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

        self.save()
        
        if groups and len(groups) == 1:
            self.create_associated_objects(extra_attributes)

        return Result(
            success=True,
            message=_("User has been created successfully."),
        )
    
    def create_associated_objects(self, associated_object_attributes={}):
        model_mapping = lava_settings.GROUPS_ASSOCIATED_MODELS
        groups = self.groups.all()
        if groups.count() != 1:
            return Result(
                success=False,
                message=_("This functionnality is not valid for a user that belongs to many.")
            )
        group = groups.first()
        if group.name in model_mapping.keys():
            class_name = model_mapping[group.name]
            klass = apps.get_model(class_name)
            if 'create' in dir(klass):
                object = klass(user=self)
                result = object.create(**associated_object_attributes)
                if not result.success:
                    raise Exception(result.message)
            else:
                object = klass(user=self, **associated_object_attributes)
                object.save()
    
    def update(self, update_fields=None):
        self.save(update_fields=update_fields)
        return Result(
            success=True,
            message=_("User has been updated successfully.")
        )
    
    def delete(self):
        super().delete()
        return Result(
            success=True,
            message=_("User has been deleted successfully")
        )


class Notification(models.Model):

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
    
    # empty sender means that the notification was generated by the system.
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(_("Date sent"), auto_now_add=True)
    title = models.CharField(_("Title"), max_length=128)
    content = models.TextField(_("Content"), blank=True, default='')
    category = models.CharField(
        _("Category"), max_length=32, default='alert',
        choices=lava_settings.NOTIFICATION_CATEGORY_CHOICES
    )
    target_groups = models.JSONField(_("Target groups"), default=list, blank=True)
    target_users = models.JSONField(_("Target users"), default=list, blank=True)

    def create(self, request=None):
        if request:
            self.sender = get_user(request)
        self.save()
