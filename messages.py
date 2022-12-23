from django.utils.translation import ugettext_lazy as _


UNKNOWN_ERROR_MESSAGE = _(
    "An error has occurred in the application. Please try again later, "
    "we are working hard to fix it as soon as possible."
)

UNIMPLEMENTED_MESSAGE = _("This operation is not yet implemented!")

CONNECTION_ERROR_MESSAGE = _(
    "Error establishing connection. Please check your connection and try again."
)

FORBIDDEN_MESSAGE = _(
    "You don't have the necessary permessions to execute this action!"
)
HTTP_403_MESSAGE = {"detail": FORBIDDEN_MESSAGE}
