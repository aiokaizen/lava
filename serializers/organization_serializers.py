from django.utils.translation import gettext_lazy as _

from rest_framework import  serializers
from rest_framework.serializers import empty

from lava.serializers import ReadOnlyBaseModelSerializer, BaseModelSerializer, UserExerptSerializer
from lava.models import Entity


# class EntityPreferencesSerializer(serializers.Serializer):

#     monthly_target = serializers.IntegerField(label=_("Monthly target"), required=False)

#     class Meta:
#         model = Entity
#         fields = [
#             'monthly_target',
#         ]


# class EntityExerptSerializer(ReadOnlyBaseModelSerializer):

#     class Meta:
#         model = Entity
#         fields = [
#             'id',
#             'name',
#             'logo',
#         ]


# class EntityGetSerializer(ReadOnlyBaseModelSerializer):

#     created_by = UserExerptSerializer()
#     address = serializers.SerializerMethodField(
#         label=_("Address"), required=False
#     )
#     transaction_volume = serializers.DecimalField(
#         source="bank_account.balance", max_digits=12, decimal_places=2, required=False
#     )


#     class Meta:
#         model=Entity
#         fields = [
#             'id',
#             'name',
#             'logo',
#             'logo_light',
#             'address',
#             'phone_number',
#             'phone_number2',
#             'email',
#             'website',
#             'transaction_volume',
#             'note',
#             'preferences',
#             'created_at',
#             'created_by',
#             'last_updated_at',
#             'deleted_at'
#         ]
#         extra_kwargs = {
#             "created_at": {"format": "%Y/%m/%d %H:%M:%S"},
#             "last_updated_at": {"format": "%Y/%m/%d %H:%M:%S"},
#             "deleted_at": {"format": "%Y/%m/%d %H:%M:%S"},
#         }

#     def get_address(self, instance):
#         return str(instance.address) if instance.address else ""


# class EntityListSerializer(ReadOnlyBaseModelSerializer):

#     address = serializers.SerializerMethodField(
#         label=_("Address"), required=False
#     )
#     transaction_volume = serializers.DecimalField(
#         source="bank_account.balance", max_digits=12, decimal_places=2, required=False
#     )

#     class Meta:
#         model=Entity
#         fields = [
#             'id',
#             'name',
#             'logo',
#             'logo_light',
#             'transaction_volume',
#             'address',
#             'phone_number',
#             'phone_number2',
#             'email',
#             'website',
#         ]

#     def get_address(self, instance):
#         return str(instance.address) if instance.address else ""


# class EntityCreateUpdateSerializer(BaseModelSerializer):

#     street_address = serializers.CharField(
#         label=_("Adresse"), source='address.street_address', required=False
#     )
#     postal_code = serializers.CharField(
#         label=_("Code postal"), source='address.postal_code', required=False
#     )
#     city = serializers.CharField(
#         label=_("Ville"), source='address.city', required=False
#     )
#     country = serializers.CharField(
#         label=_("Pays"), source='address.country', required=False
#     )

#     class Meta:
#         model=Entity
#         fields = [
#             'name',
#             'logo',
#             'logo_light',
#             'address',
#             'street_address',
#             'postal_code',
#             'city',
#             'country',
#             'phone_number',
#             'phone_number2',
#             'email',
#             'website',
#             'note',
#         ]

#     def validate(self, attrs):
#         validated_data = super().validate(attrs)
#         address_data = validated_data.pop("address", None)

#         if address_data:
#             instance = getattr(self, 'instance', None)
#             old_address = getattr(instance, 'address', None)
#             address_serializer = AddressSerializer(
#                 instance=old_address, data=address_data
#             )
#             address_serializer.is_valid(raise_exception=True)
#             address_serializer.save()
#             validated_data["address"] = address_serializer.instance

#         return validated_data


# class EntityImportExportSerializer(EntityCreateUpdateSerializer):

#     created_by = serializers.SerializerMethodField(label="Crée par", required=False)

#     class Meta:
#         model=Entity
#         fields = [
#             'name',
#             'street_address',
#             'postal_code',
#             'city',
#             'country',
#             'phone_number',
#             'phone_number2',
#             'email',
#             'website',
#             'note',
#             'created_at',
#             'created_by',
#             'last_updated_at',
#             'deleted_at'
#         ]
#         read_only_fields = [
#             'created_at',
#             'created_by',
#             'last_updated_at',
#             'deleted_at'
#         ]
#         extra_kwargs = {
#             "created_at": {"format": "%m/%d/%Y %H:%M"},
#             "last_updated_at": {"format": "%m/%d/%Y %H:%M"},
#             "deleted_at": {"format": "%m/%d/%Y %H:%M"},
#         }

#     def get_created_by(self, instance):
#         if instance.created_by:
#             return f"{instance.created_by.first_name} {instance.created_by.last_name}"
#         return '---'
