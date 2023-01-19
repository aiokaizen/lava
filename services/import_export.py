import os
from datetime import datetime

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from lava.utils import Result
from lava.models import Permission, Group

from openpyxl import Workbook
from openpyxl.utils import units
from openpyxl.writer import excel


def export_permissions(filename=None):
    """
    This function creates a tmp file that contains all the groups and the 
    permissions affected to them and returns a result that has the tmp file path
    as it's instance.
    """

    wb = Workbook()
    ws = wb.active

    ws.title = "Permissions"
    
    permissions = Permission.objects.all()
    groups = Group.objects.all()
    
    ws.cell(row=1, column=1, value="Permissions")

    for index, permission in enumerate(permissions):
        ws.cell(row=index + 2, column=1, value=permission.name)

    for index, group in enumerate(groups):
        ws.cell(row=1, column=index + 2, value=group.name.upper())

    for row, permission in enumerate(permissions):
        for col, group in enumerate(groups):
            has_perm = permission in group.permissions.all()
            value = 'X' if has_perm else ''
            ws.cell(row=row + 2, column=col + 2, value=value)

    # cell = ws.cell(1, 1)
    # print('cell:', cell)
    # ws.freeze_panes(cell)
   
    filename = filename or f'permissions_{int(datetime.now().strftime("%Y%m%d%H%M%S"))}.xlsx'
    tmp_file_path = os.path.join(settings.TMP_ROOT, filename)

    saved = excel.save_workbook(wb, tmp_file_path)
    if not saved:
        return Result(False, _("The tmp file could not be created!"))

    return Result(True, _("File exported successfully"), instance=tmp_file_path)
