from django.shortcuts import reverse, redirect
from django.conf import settings


class MaintenanceModeMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.META.get('PATH_INFO', "")
        query = request.META.get('QUERY_STRING', "")

        if settings.MAINTENANCE_BYPASS_QUERY in query:
            request.session['bypass_maintenance'] = True
        elif 'bypass_maintenance' in request.session:
            # This section resets bypass param each time it's not passed in the request.
            # This behaviour can be changed to require the bypass password only
            # once (In the login page for example)
            # del request.session['bypass_maintenance']
            pass

        if not request.session.get('bypass_maintenance', False):
            if settings.MAINTENANCE_MODE and path != reverse("api-maintenance"):
                response = redirect(reverse("api-maintenance"))
                return response

        response = self.get_response(request)

        return response