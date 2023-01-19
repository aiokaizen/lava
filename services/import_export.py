import os
from copy import copy
from datetime import datetime

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from lava.utils import Result, get_tmp_root
from lava.models import Permission, Group

from openpyxl import Workbook
from openpyxl.utils import units
from openpyxl.writer import excel
from openpyxl.styles.fonts import Font
from openpyxl.styles.named_styles import NamedStyle
from openpyxl.styles.alignment import Alignment
from openpyxl.styles.fills import PatternFill
from openpyxl.styles.borders import Border, Side


def export_permissions(filename=None):
    """
    This function creates a tmp file that contains all the groups and the 
    permissions affected to them and returns a result that has the tmp file path
    as it's instance.
    """

    wb = Workbook()
    ws = wb.active

    # Fonts
    default_font = Font(sz=14, bold=False, color="11123a")
    header_font = Font(sz=14, bold=True, color="11123a")

    # Borders
    default_side = Side(color="000000", style="thin")
    header_side = Side(color="000000", style="thin")
    default_border = Border(
        left=default_side, right=default_side, top=default_side, bottom=default_side, diagonal=default_side
    )
    header_border = Border(
        left=header_side, right=header_side, top=header_side, bottom=header_side, diagonal=header_side
    )

    # Styles
    default_style = NamedStyle(
        name="default",
        font=copy(default_font),
        border=copy(default_border),
        alignment=Alignment(horizontal="left", vertical="center"),
        fill=PatternFill(fill_type="solid", fgColor="e5f3f1"),
        builtinId=1
    )

    header_style = NamedStyle(
        name="header",
        font=copy(header_font),
        border=copy(header_border),
        alignment=Alignment(horizontal="center", vertical="center"),
        # fill=PatternFill(fill_type="solid", fgColor="1cab98"),
        fill=PatternFill(fill_type="solid", fgColor="7ccbc0"),
        builtinId=1
    )

    wb.add_named_style(default_style)
    wb.add_named_style(header_style)
    ws.title = "Permissions"
    ws.row_dimensions[1].height = 40
    
    permissions = Permission.objects.all()
    groups = Group.objects.all()
    
    a1 = ws.cell(row=1, column=1, value="Permissions")
    a1.style = 'header'
    

    for index, permission in enumerate(permissions):
        cell = ws.cell(row=index + 2, column=1, value=permission.name)
        cell.style = 'header'
        cell.alignment = Alignment(horizontal="left", vertical="center")

    for index, group in enumerate(groups):
        cell = ws.cell(row=1, column=index + 2, value=group.name.upper())
        cell.style = 'header'

    for row, permission in enumerate(permissions):
        for col, group in enumerate(groups):
            has_perm = permission in group.permissions.all()
            value = 'X' if has_perm else ''
            cell = ws.cell(row=row + 2, column=col + 2, value=value)
            cell.style = 'default'
            cell.alignment = Alignment(horizontal="center", vertical="center")

    # cell = ws.cell(1, 1)
    # print('cell:', cell)
    # ws.freeze_panes(cell)
   
    filename = filename or f'permissions_{int(datetime.now().strftime("%Y%m%d%H%M%S"))}.xlsx'
    tmp_file_path = os.path.join(get_tmp_root(), filename)

    saved = excel.save_workbook(wb, tmp_file_path)
    if not saved:
        return Result(False, _("The tmp file could not be created!"))

    return Result(True, _("File exported successfully"), instance=tmp_file_path)
