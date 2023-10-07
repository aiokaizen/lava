from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from lava.enums import DeletePolicy
from lava.models import BaseModel
from lava.validators import validate_empty_field
from lava.utils import get_document_filename


class Address(BaseModel):

    create_success_message = _("L'adresse a été créée avec succès.")
    update_success_message = _("L'adresse a été modifiée avec succès")
    delete_success_message = _("L'addresse a été supprimée avec succès.")
    default_delete_policy = DeletePolicy.HARD_DELETE

    class Meta(BaseModel.Meta):
        verbose_name = _("Adresse")
        verbose_name_plural = _("Adresses")
        ordering = ("city", "country", "street_address")

    street_address = models.CharField(_("Adresse"), max_length=256, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=256, blank=True)
    city = models.CharField(
        _("Ville"), max_length=256, validators=[validate_empty_field]
    )
    country = models.CharField(
        _("Pays"), max_length=256, validators=[validate_empty_field]
    )

    def __str__(self):
        if self.street_address:
            return f"{self.street_address},\r\n{self.city} {self.postal_code}, {self.country}"
        else:
            return f"{self.city} {self.postal_code}, {self.country}"

    def in_use(self):
        """returns True if the address is already used in the system."""
        for field in self._meta.get_fields():
            if not isinstance(field, models.ForeignObjectRel):
                continue

            if field.multiple:  # ManyToOne or ManyToMany Relation
                if getattr(self, field.get_accessor_name()).exists():
                    return True
            else:  # OneToOne Relation
                if getattr(self, field.get_accessor_name(), None):
                    return True

        return False

    @classmethod
    def get_filter_params(cls, kwargs=None):

        filter_params = Q()

        if kwargs is None:
            kwargs = {}

        if "query" in kwargs:
            filter_params &= Q(city__icontains=kwargs.get("query")) | Q(
                country__icontains=kwargs.get("query")
            )

        if "city" in kwargs:
            filter_params &= Q(city__icontains=kwargs.get("city"))

        if "country" in kwargs:
            filter_params &= Q(country__icontains=kwargs.get("country"))

        return filter_params

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = cls.get_filter_params(kwargs)
        base_queryset = super().filter(user=user, kwargs=kwargs)
        queryset = base_queryset.filter(filter_params)
        return queryset


class FileDocument(BaseModel):
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    name = models.CharField(_("Name"), max_length=256, default="", blank=True)
    document_file = models.FileField(_("File"), upload_to=get_document_filename)

    def __str__(self):
        return self.name


# class SocialMediaAccount(BaseModel):

#     class Meta:
#         verbose_name = _("Social media account")
#         verbose_name_plural = _("Social media accounts")

#     name = models.CharField(_("Social media name"), max_length=32)
#     username = models.CharField(_("Social media username"), max_length=128)
#     url = models.URLField(_("Social media url"), null=True, blank=True)

#     def __str__(self):
#         return self.name + (f'@{self.username}' if self.username else '')


# class SocialMediaAccounts(BaseModel):

#     class Meta:
#         verbose_name = _("Social media accounts")
#         verbose_name_plural = _("Social media accounts")

#     facebook = models.OneToOneField(
#         SocialMediaAccount, verbose_name=_("Facebook"), on_delete=models.SET_NULL
#     )
#     youtube = models.OneToOneField(
#         SocialMediaAccount, verbose_name=_("Youtube"), on_delete=models.SET_NULL
#     )
#     instagram = models.OneToOneField(
#         SocialMediaAccount, verbose_name=_("Instagram"), on_delete=models.SET_NULL
#     )
#     linkedin = models.OneToOneField(
#         SocialMediaAccount, verbose_name=_("LinkedIn"), on_delete=models.SET_NULL
#     )
#     pinterest = models.OneToOneField(
#         SocialMediaAccount, verbose_name=_("Pinterest"), on_delete=models.SET_NULL
#     )
#     dribbble = models.OneToOneField(
#         SocialMediaAccount, verbose_name=_("Dribbble"), on_delete=models.SET_NULL
#     )

#     def __str__(self):
#         return "Social media accounts"

#     def create(self, *args, **kwargs):
#         self.facebook = self.facebook or (
#             SocialMediaAccount(name="Facebook").create().instance
#         )
#         self.youtube = self.youtube or (
#             SocialMediaAccount(name="Youtube").create().instance
#         )
#         self.instagram = self.instagram or (
#             SocialMediaAccount(name="Instagram").create().instance
#         )
#         self.linkedin = self.linkedin or (
#             SocialMediaAccount(name="Linked In").create().instance
#         )
#         self.pinterest = self.pinterest or (
#             SocialMediaAccount(name="Pinterest").create().instance
#         )
#         self.dribbble = self.dribbble or (
#             SocialMediaAccount(name="Dribbble").create().instance
#         )
#         result = super().create(*args, **kwargs)
#         return result


# class ContactInfo(BaseModel):

#     class Meta:
#         verbose_name = _("Contact info")
#         verbose_name_plural = _("Contacts info")

#     phone_number = models.CharField(_("Phone number"), max_length=32, default="", blank=True)
#     phone_number2 = models.CharField(_("Phone numbser 2"), max_length=32, default="", blank=True)
#     email = models.EmailField(_("E-mail"), default="", blank=True)
#     website = models.URLField(_("Website"), null=True, blank=True)

#     def __str__(self):
#         return self.phone_number or self.phone_number2 or self.email or self.website
