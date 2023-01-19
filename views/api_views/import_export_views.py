from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from lava.services import class_permissions as lava_permissions
from lava.services import import_export


class ExportPermissions(APIView):

    permission_classes = []

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        if self.request.method == 'GET':
            permission_classes = [lava_permissions.CanExportPermissions]
        return [permission() for permission in permission_classes]
    
    def get(self, request, *args, **kwargs):

        result = import_export.export_permissions()
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        
        filename = result.instance

        with open(filename, 'rb') as xlfile:

            response = HttpResponse(xlfile, content_type='application/xlsx')
            response["content-disposition"] = f"attachment; filename=permissions.xlsx"

            return response
