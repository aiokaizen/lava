from rest_framework.fields import ImageField

from easy_thumbnails.files import get_thumbnailer


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
