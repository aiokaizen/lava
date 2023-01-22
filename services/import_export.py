from django.utils.translation import gettext_lazy as _

from lava.models import Permission, Group
from lava.utils.utils import Result
from lava.utils.xlsx_utils import ExportDataType, export_xlsx


def export_permissions():
    """
    This function creates a tmp file that contains all the groups and the 
    permissions affected to them and returns a result that has the tmp file path
    as it's instance.
    """

    permissions = Permission.objects.all()
    groups = Group.objects.all().order_by("name")
    header_title = str(_("List of available permissions"))
    description = str(_(
        "Note: Please Fill in the cells with 'X' to provide groups "
        "with their permissions."
    ))

    rows = permissions.values_list("name", flat=True)
    columns = [ name.upper() for name in groups.values_list("name", flat=True)]
    columns = ["Permissions", *columns]
    data_content = []

    for permission in permissions:
        perms = []
        for group in groups:
            has_perm = permission in group.permissions.all()
            value = 'X' if has_perm else ''
            perms.append(value)
        data_content.append(perms)
    
    data = ExportDataType(
        row_titles=rows,
        col_titles=columns,
        data=data_content
    )
    
    result = export_xlsx(
        data,
        header_title=header_title,
        description=description,
        sheet_title="Permissions",
        freeze_header=False,
        remove_cells_borders=False,
        title_section_length=6,
    )

    if result.is_error:
        return result

    return Result(True, _("File exported successfully"), instance=result.instance)
