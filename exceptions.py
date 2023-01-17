from django.utils.translation import gettext_lazy as _


class LavaBaseException(Exception):

    def __init__(self, result):
        message = result.message
        self.message = message
        super().__init__(self.message)
