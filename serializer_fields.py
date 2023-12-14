from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from rest_framework.fields import ImageField, FileField, empty

from easy_thumbnails.files import get_thumbnailer


KILO = 2**10
MEGA = KILO**2
GIGA = MEGA**2
TERA = GIGA**2


def humanize_file_size(file_size):  # File size in bytes
    if file_size < KILO:
        return f"{file_size} Byte"
    elif file_size < MEGA:
        return f"{(file_size / KILO):.2f} KB"
    elif file_size < GIGA:
        return f"{(file_size / MEGA):.2f} MB"
    elif file_size < TERA:
        return f"{(file_size / GIGA):.2f} GB"

    return f"{file_size / TERA} TB"


class ThumbnailImageField(ImageField):
    def __init__(self, alias=None, options=None, **kwargs):
        self.alias = alias
        self.options = options
        super().__init__(**kwargs)

    def to_representation(self, value):
        if not value:
            return None

        if self.options and not self.alias:
            value = get_thumbnailer(value).get_thumbnail(self.options)
        elif self.alias:
            value = value[self.alias]

        return super().to_representation(value)


class ControlledFileField(FileField):
    def __init__(self, max_size=MEGA, **kwargs):
        self.max_size = max_size  # max_size in Mb
        super().__init__(**kwargs)

    def run_validation(self, data=empty):
        # Validation
        file = data
        if file is not empty and file.size > self.max_size: 
            raise ValidationError(
                _(
                    "The size of the file you uploaded (%(file_size)s) exceeds the maximum allowed size of %(max_size)s."
                    % {
                        "file_size": humanize_file_size(file.size),
                        "max_size": humanize_file_size(self.max_size),
                    }
                )
            )
        return super().run_validation(data)


# Default callabels for serializer fields


class NotificationGroupsDefault:
    """
    Returns a list of the user's notification groups.
    """

    requires_context = True

    def __call__(self, serializer_field):
        instance = serializer_field.context.get("instance")
        if not instance:
            return []
        return instance.get_notification_groups_ids()
