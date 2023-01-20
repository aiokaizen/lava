import os
from copy import copy
from datetime import datetime

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from lava.utils import Result, get_tmp_root, map_interval
from lava.models import Permission, Group

from openpyxl import Workbook
from openpyxl.utils import units, get_column_letter
from openpyxl.writer import excel
from openpyxl.styles.fonts import Font
from openpyxl.styles.named_styles import NamedStyle
from openpyxl.styles.alignment import Alignment
from openpyxl.styles.fills import PatternFill
from openpyxl.styles.borders import Border, Side


def export_permissions():
    """
    This function creates a tmp file that contains all the groups and the 
    permissions affected to them and returns a result that has the tmp file path
    as it's instance.
    """

    wb = Workbook()
    ws = wb.active

    start_row_index = 4
    start_col_index = 2

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
    logo_filepath = os.path.join(settings.BASE_DIR, 'lava/static/lava/assets/images/logo/logo.png')

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
        fill=PatternFill(fill_type="solid", fgColor="7ccbc0"),
        builtinId=1
    )

    wb.add_named_style(default_style)
    wb.add_named_style(header_style)
    ws.title = "Permissions"
    ws.row_dimensions[start_row_index].height = 40
    
    permissions = Permission.objects.all()
    groups = Group.objects.all().order_by("name")
    
    start_cell = ws.cell(row=start_row_index, column=start_col_index, value="Permissions")
    start_cell.style = 'header'
    start_col_name = get_column_letter(start_col_index)
    start_column = ws.column_dimensions[start_col_name]
    start_column.width = get_col_width(start_cell.value, header_font.sz)
    
    max_col_width = start_column.width
    for index, permission in enumerate(permissions):
        cell = ws.cell(row=index + start_row_index + 1, column=start_col_index, value=permission.name)
        cell.style = 'header'
        cell.alignment = Alignment(horizontal="left", vertical="center")

        col_width = get_col_width(cell.value, header_font.sz)
        if col_width > max_col_width:
            start_column.width = col_width
            max_col_width = col_width

    for index, group in enumerate(groups):
        group_name = group.name.upper()
        cell = ws.cell(row=start_row_index, column=index + start_col_index + 1, value=group_name)
        cell.style = 'header'
        col_name = get_column_letter(start_col_index + index + 1)
        ws.column_dimensions[col_name].width = get_col_width(group_name, header_font.sz)

    for row, permission in enumerate(permissions):
        for col, group in enumerate(groups):
            has_perm = permission in group.permissions.all()
            value = 'X' if has_perm else ''
            cell = ws.cell(row=row + start_row_index + 1 , column=col + start_col_index + 1, value=value)
            cell.style = 'default'
            cell.alignment = Alignment(horizontal="center", vertical="center")

    # cell = ws.cell(1, 1)
    # print('cell:', cell)
    # ws.freeze_panes(cell)
   
    filename = f'permissions_{int(datetime.now().strftime("%Y%m%d%H%M%S"))}.xlsx'
    tmp_file_path = os.path.join(get_tmp_root(), filename)

    saved = excel.save_workbook(wb, tmp_file_path)
    if not saved:
        return Result(False, _("The tmp file could not be created!"))

    return Result(True, _("File exported successfully"), instance=tmp_file_path)


def get_col_width(content, font_size):
    content_length = len(content)
    min_fs, max_fs = 10, 36
    min_width = 2
    max_width = 8 - map_interval(content_length, 5, 20, 1, 8)

    width_per_char = map_interval(font_size, min_fs, max_fs, min_width, max_width)
    width = width_per_char * content_length

    return max(round(width, 2), 15.83)
