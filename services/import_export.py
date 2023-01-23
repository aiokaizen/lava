from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext as __
from django.contrib.admin.models import LogEntry as BaseLogEntryModel
from django.db.models import Q

from lava.models import Permission, Group
from lava.models.models import LogEntry
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
    header_title = __("List of available permissions")
    description = __(
        "Note: Please Fill in the cells with 'X' to provide groups "
        "with their permissions."
    )

    rows = permissions.values_list("name", flat=True)
    columns = [name.upper() for name in groups.values_list("name", flat=True)]
    columns = [__("Permissions"), *columns]
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
        sheet_title=__("Permissions"),
        freeze_header=False,
        remove_cells_borders=False,
        title_section_length=6,
    )

    if result.is_error:
        return result

    return Result(True, _("File exported successfully"), instance=result.instance)


def export_activity_journal(
    user=None, start_date=None, end_date=None,
    content_type='', action_type=0, use_base_entry_model=True
):
    """
    This function creates a tmp file that contains journal of all
    registered actions in the system.

    :content_type:str:app_name.class_name. ex: lava.User
    """

    filters = Q()
    if user:
        filters |= Q(user=user)
    if start_date and end_date:
        filters |= Q(action_time__gte=start_date) & Q(action_time__lte=end_date)
    elif start_date:
        filters |= Q(action_time__gte=start_date)
    elif end_date:
        filters |= Q(action_time__lte=end_date)
    if action_type:
        filters |= Q(action_flag=action_type)
    if content_type:
        app_name, model = content_type.split('.')
        filters |= (
            Q(content_type__app_label=app_name) &
            Q(content_type__model=model)
        )

    LogEntryModel = BaseLogEntryModel if use_base_entry_model else LogEntry
    journal = LogEntryModel.objects.filter(filters)

    header_title = __("Activity journal")
    description = __(
        "This is the list of actions that were performed in the system."
    )

    columns = [
        __("Action time"),
        __("User"),
        # __("User ID"),
        __("Action"),
        __("Content type"),
        __("Object name"),
        __("Object ID"),
        __("Message")
    ]
    data_content = []

    for action in journal:
        data_content.append([
            action.action_time.strftime("%d/%m/%Y %H:%M:%S"),
            f"{action.user.first_name} {action.user.last_name}",
            # action.user.id,
            action.get_action_flag_display(),
            action.content_type.model.upper(),
            action.object_repr,
            action.object_id,
            action.change_message
        ])
    
    data = ExportDataType(
        col_titles=columns,
        data=data_content
    )
    
    result = export_xlsx(
        data,
        header_title=header_title,
        description=description,
        sheet_title=__("Activities"),
        freeze_header=False,
        remove_cells_borders=False,
        title_section_length=6,
    )

    if result.is_error:
        return result

    return Result(True, _("File exported successfully"), instance=result.instance)
