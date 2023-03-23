from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from lava.enums import DeletePolicy
from lava.models import BaseModel
from lava.validators import validate_empty_field


class Address(BaseModel):

    create_success_message = _("L'adresse a été créée avec succès.")
    update_success_message = _("L'adresse a été modifiée avec succès")
    delete_success_message = _("L'addresse a été supprimée avec succès.")
    default_delete_policy = DeletePolicy.HARD_DELETE

    class Meta(BaseModel.Meta):
        verbose_name = _("Adresse")
        verbose_name_plural = _("Adresses")
        ordering = ('city', 'country', 'street_address')

    street_address = models.CharField(_("Adresse"), max_length=256, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=256, blank=True)
    city = models.CharField(_("Ville"), max_length=256, validators=[validate_empty_field])
    country = models.CharField(_("Pays"), max_length=256, validators=[validate_empty_field])

    def __str__(self):
        if self.street_address:
            return f"{self.street_address},\r\n{self.city} {self.postal_code}, {self.country}"
        else:
            return f"{self.city} {self.postal_code}, {self.country}"

    def in_use(self):
        """ returns True if the address is already used in the system. """
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
            filter_params &= (
                Q(city__icontains=kwargs.get("query")) |
                Q(country__icontains=kwargs.get("query"))
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
