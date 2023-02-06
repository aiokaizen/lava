from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.http import Http404

from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework import status

from lava.messages import (
    FORBIDDEN_MESSAGE, NOT_AUTHENTICATED_MESSAGE, UNKNOWN_ERROR_MESSAGE, NOT_FOUND_MESSAGE
)
from lava.error_codes import (
    PERMISSION_DENIED_ERROR_CODE, NOT_AUTHENTICATED_ERROR_CODE, UNKNOWN,
    NOT_FOUND_ERROR_CODE
)


class LavaBaseException(Exception):

    def __init__(self, result):
        message = result.message
        self.message = message
        super().__init__(self.message)


def lava_drf_exception_handler(exc, context):
    from lava.utils import Result

    if isinstance(exc, NotAuthenticated):
        return Response(
            Result(False, NOT_AUTHENTICATED_MESSAGE, error_code=NOT_AUTHENTICATED_ERROR_CODE).to_dict(),
            status=status.HTTP_401_UNAUTHORIZED
        )
    elif isinstance(exc, PermissionDenied):
        return Response(
            Result(False, FORBIDDEN_MESSAGE, error_code=PERMISSION_DENIED_ERROR_CODE).to_dict(),
            status=status.HTTP_403_FORBIDDEN
        )

    # if settings.DEBUG == False and isinstance(exc, Exception):
    #     return Response(
    #         Result(False, UNKNOWN_ERROR_MESSAGE, error_code=UNKNOWN).to_dict(),
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )

    return exception_handler(exc, context)