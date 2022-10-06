from django.utils.translation import ugettext_lazy as _


UNIMPLEMENTED_MESSAGE = _("This operation is not yet implemented!")

CONNECTION_ERROR_MESSAGE = _(
    "Error establishing connection. Please check your connection and try again."
)

FORBIDDEN_MESSAGE = _(
    "You don't have the necessary permessions to execute this action!"
)
HTTP_403_MESSAGE = {"detail": FORBIDDEN_MESSAGE}
