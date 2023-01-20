import os
from copy import copy
from datetime import datetime

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from lava.utils import Result, get_tmp_root, map_interval
from lava.models import Permission, Group
from lava.styles import XLSXStyles

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.writer import excel
from openpyxl.styles.alignment import Alignment
from openpyxl.drawing.image import Image
from PIL import Image as PILImage


def get_col_width(content, font_size):
    content_length = len(content)
    min_fs, max_fs = 10, 36
    min_width = 2
    max_width = 8 - map_interval(content_length, 5, 20, 1, 8)

    width_per_char = map_interval(font_size, min_fs, max_fs, min_width, max_width)
    width = width_per_char * content_length

    return max(round(width, 2), 15.83)


def get_image(image_path, target_width=None, target_height=None):

    image = PILImage.open(image_path)
    tmp_image_filename = os.path.join(get_tmp_root(), f"tmp_excel_logo.png")

    if target_width and target_width != image.width:
        target_height = int(image.height * target_width / image.width)
        image = image.resize(size=(target_width, target_height))
        image.save(tmp_image_filename)
        image.close()
        image = PILImage.open(tmp_image_filename)

    elif target_height and target_height != image.height:
        target_width = int(image.width * target_height / image.height)
        image = image.resize(size=(target_width, target_width))
        image.save(tmp_image_filename)
        image.close()
        image = PILImage.open(tmp_image_filename)
    
    return image


def export_permissions():
    """
    This function creates a tmp file that contains all the groups and the 
    permissions affected to them and returns a result that has the tmp file path
    as it's instance.
    """

    logo = None
    logo_filepath = os.path.join(settings.BASE_DIR, 'lava/static/lava/assets/images/logo/logo.png')
    styles = XLSXStyles()

    start_row_index = 4
    start_col_index = 2
        
    permissions = Permission.objects.all()
    groups = Group.objects.all().order_by("name")

    try:
        # Workbook initialization
        wb = Workbook()
        wb.add_named_style(styles.base_style)
        wb.add_named_style(styles.default_style)
        wb.add_named_style(styles.header_style)
        wb.add_named_style(styles.title_style)

        # Sheet setup
        ws = wb.active
        ws.title = "Permissions"

        ws.row_dimensions[start_row_index].height = 40
        ws.row_dimensions[2].height = 40
        ws.row_dimensions[3].height = 40

        ws.merge_cells('B2:B3')
        ws.merge_cells('C2:I2')
        ws.merge_cells('C3:I3')

        start_cell = ws.cell(row=start_row_index, column=start_col_index, value="Permissions")
        start_cell.style = 'header'

        start_col_name = get_column_letter(start_col_index)
        start_column = ws.column_dimensions[start_col_name]
        start_column.width = get_col_width(start_cell.value, styles.fonts.header.sz)

        title_cell = ws.cell(row=2, column=3, value="List of all available permissions")
        title_cell.style = 'title'

        description_cell = ws.cell(
            row=3, column=3,
            value=str(_(
                "HOW TO USE: Lorem ipsum dolor sit amet consectetur adipisicing elit. Iusto sed "
                "delectus iure, rerum laboriosam sit aliquid! Eaque fuga incidunt sapiente ab "
                "consectetur eos provident saepe, odio obcaecati? Quibusdam quos perferendis neque. "
                "Inventore hic mollitia quam minus deleniti. Quibusdam, quaerat deleniti?"
            ))
        )
        description_cell.style = 'base'
        
        logo = get_image(logo_filepath, target_width=250)
        ws.add_image(Image(logo), 'B2')
        
        max_col_width = start_column.width
        for index, permission in enumerate(permissions):
            cell = ws.cell(row=index + start_row_index + 1, column=start_col_index, value=permission.name)
            cell.style = 'header'
            cell.alignment = Alignment(horizontal="left", vertical="center")

            col_width = get_col_width(cell.value, styles.fonts.header.sz)
            if col_width > max_col_width:
                start_column.width = col_width
                max_col_width = col_width

        for index, group in enumerate(groups):
            group_name = group.name.upper()
            cell = ws.cell(row=start_row_index, column=index + start_col_index + 1, value=group_name)
            cell.style = 'header'
            col_name = get_column_letter(start_col_index + index + 1)
            ws.column_dimensions[col_name].width = get_col_width(group_name, styles.fonts.header.sz)

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
    finally:
        if logo:
            logo.close()

    if not saved:
        return Result(False, _("The tmp file could not be created!"))

    return Result(True, _("File exported successfully"), instance=tmp_file_path)
