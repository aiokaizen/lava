from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from colorfield.fields import ColorField

from lava import settings as lava_settings
from lava.enums import DeletePolicy
from lava.models.base_models import BaseModel
from lava.models.utility_models import Address
from lava.utils import (
    get_entity_logo_filename, get_entity_logo_light_filename,
    Result, adjust_color
)


class Account(BaseModel):

    create_success_message = _("The account has been created successfully.")
    update_success_message = _("The account has been updated successfully.")
    delete_success_message = _("The account has been deleted successfully.")
    default_delete_policy = DeletePolicy.HARD_DELETE

    class Meta(BaseModel.Meta):
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        abstract = True

    name = models.CharField(_("Name"), max_length=256, unique=True, null=True, blank=True)
    balance = models.DecimalField(_("Balance"), max_digits=14, decimal_places=2, default=0, blank=True)

    def __str__(self):
        return f"{self.name}"

    def debit_account(self, user, amount):
        if not amount:
            return Result.warning(_("Amount equals to 0. Account not debitted."))

        self.balance -= Decimal(amount)
        result = self.update(user, update_fields=["balance"], message="Debit Account")
        if result.is_error:
            return result
        return Result.success(_("Account has been debitted successfully."))

    def credit_account(self, user, amount):
        if not amount:
            return Result.warning(_("Amount equals to 0. Account not creditted."))

        self.balance += Decimal(amount)
        result = self.update(user, update_fields=["balance"], message="Credit Account")
        if result.is_error:
            return result
        return Result.success(_("Account has been creditted successfully."))


class Bank(BaseModel):

    create_success_message = _("The bank has been created successfully.")
    update_success_message = _("The bank has been updated successfully.")
    delete_success_message = _("The bank has been deleted successfully.")
    default_delete_policy = DeletePolicy.HARD_DELETE

    class Meta(BaseModel.Meta):
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")
        ordering = ('name', )
        abstract = not lava_settings.ACTIVATE_PAYEMENTS

    name = models.CharField(_("Name"), max_length=256, unique=True)
    country = models.CharField(_("Country"), max_length=256, default='Morocco', blank=True)
    routing_number = models.CharField(_("Routing number"), max_length=9, blank=True)
    swift_code = models.CharField(_("BIC / SWIFT"), max_length=256, blank=True)

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def create_default_bank(cls):
        pass


class BankAccount(Account):

    create_success_message = _("The bank account has been created successfully.")
    update_success_message = _("The bank account has been updated successfully.")
    delete_success_message = _("The bank account has been deleted successfully.")
    default_delete_policy = DeletePolicy.HARD_DELETE

    class Meta(BaseModel.Meta):
        verbose_name = _("Bank account")
        verbose_name_plural = _("Bank accounts")
        abstract = not lava_settings.ACTIVATE_PAYEMENTS

    account_holder = models.CharField(_("Account holder"), max_length=256, blank=True)
    iban = models.CharField(_("Code postal"), max_length=34, blank=True)
    rib = models.CharField(_("RIB"), max_length=24, blank=True)
    bank = models.ForeignKey(Bank, verbose_name=_("Bank"), on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def get_filter_params(cls, kwargs=None):

        filter_params = Q()

        if kwargs is None:
            kwargs = {}

        if "query" in kwargs:
            filter_params &= (
                Q(city__icontains=kwargs.get("query")) |
                Q(country__icontains=kwargs.get("query"))
            )

        if "bank" in kwargs:
            filter_params &= Q(bank__icontains=kwargs.get("bank"))

        if "country" in kwargs:
            filter_params &= Q(country__icontains=kwargs.get("country"))

        return filter_params

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = cls.get_filter_params(kwargs)
        base_queryset = super().filter(user=user, trash=trash, kwargs=kwargs)
        queryset = base_queryset.filter(filter_params)
        return queryset


class Entity(BaseModel):

    class Meta(BaseModel.Meta):
        verbose_name = _("Entity")
        verbose_name_plural = _("Entities")
        abstract = True

    name = models.CharField(_("Name"), max_length=256)
    logo = models.ImageField(_("Logo"), upload_to=get_entity_logo_filename, null=True, blank=True)
    logo_light = models.ImageField(_("Logo light"), upload_to=get_entity_logo_light_filename, null=True, blank=True)
    address = models.ForeignKey(Address, verbose_name=_("Address"), on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(_("Phone number"), max_length=32, default="", blank=True)
    phone_number2 = models.CharField(_("Phone numbser 2"), max_length=32, default="", blank=True)
    email = models.EmailField(_("E-mail"), default="", blank=True)
    website = models.URLField(_("Website"), null=True, blank=True)
    note = models.TextField(_("Note"), default="", blank=True)
    accent_color = ColorField(_("Accent color"), default="", blank=True)
    bank_account = models.OneToOneField(
        BankAccount, verbose_name=_("Bank account"), null=True, blank=True, on_delete=models.PROTECT
    )

    # Legal informations
    ice = models.CharField(_("ICE"), max_length=15, null=True, blank=True)
    rc = models.CharField(_("RC"), max_length=10, null=True, blank=True)
    ifisc = models.CharField(_("IF"), max_length=10, null=True, blank=True)  # Identifiant fiscale
    tp = models.CharField(_("TP"), max_length=10, null=True, blank=True)
    preferences = models.JSONField(_("Preferences"), default=dict)
    is_current = models.BooleanField(_("Entité local"), default=False, blank=True)

    def __str__(self):
        return self.name

    def get_accent_colors(self):
        color = self.accent_color or lava_settings.EKBLOCKS_COLOR
        return {
            "primary_color": color,
            "light_color": adjust_color(color, 1),
            "dark_color": adjust_color(color, -1)
        }

    def create(self, user=None, check_address=False, *args, **kwargs):

        if self.address and check_address:
            if self.address.in_use():
                result = self.address.duplicate()
                if result.is_success:
                    self.address = result.instance

        # Create BankAccount
        if not self.bank_account:
            self.bank_account = BankAccount().create().instance

        result = super().create(user=user, *args, **kwargs)
        if result.is_error:
            return result

        return Result(True, _("The entity '%(name)s' has been successfully created." % {'name': self.name}), instance=self)

    @classmethod
    def get_filter_params(cls, kwargs=None):

        filter_params = Q()

        if kwargs is None:
            kwargs = {}

        if "query" in kwargs:
            filter_params &= (
                Q(name__icontains=kwargs.get("query"))
            )

        if "name" in kwargs:
            filter_params &= Q(name__icontains=kwargs.get("name"))

        if "city" in kwargs:
            city = kwargs["city"]
            filter_params &= Q(address__city__iexact=city)

        return filter_params

    @classmethod
    def filter(cls, user=None, trash=False, kwargs=None):
        filter_params = Entity.get_filter_params(kwargs)
        base_queryset = super().filter(user=user, trash=trash, kwargs=kwargs)
        queryset = base_queryset.filter(filter_params)
        return queryset
