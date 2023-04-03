import re

from django.shortcuts import reverse, redirect
from django.conf import settings

from rest_framework.authtoken.models import Token

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack

from lava.models import User


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.META.get("PATH_INFO", "")
        query = request.META.get("QUERY_STRING", "")

        if settings.MAINTENANCE_BYPASS_QUERY in query:
            request.session["bypass_maintenance"] = True
        elif "bypass_maintenance" in request.session:
            # This section resets bypass param each time it's not passed in the request.
            # This behaviour can be changed to require the bypass password only
            # once (In the login page for example)
            # del request.session['bypass_maintenance']
            pass

        if not request.session.get("bypass_maintenance", False):
            if settings.MAINTENANCE_MODE and path != reverse("api-maintenance"):
                response = redirect(reverse("api-maintenance"))
                return response

        response = self.get_response(request)

        return response


@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


class SocketTokenAuthMiddleware(BaseMiddleware):

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        try:
            query_string = scope["query_string"].decode("utf-8")
            match = re.search(r"token=([\w\d]+)", query_string)
            token_key = match.group(1) if match else ""

            user = await get_user(token_key)
            if user is not None:
                scope['user'] = user
        except (IndexError, ValueError, Token.DoesNotExist):
            pass
        return await super().__call__(scope, receive, send)

SocketTokenAuthMiddlewareStack = lambda inner: SocketTokenAuthMiddleware(AuthMiddlewareStack(inner))
