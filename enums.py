import enum


class DeletePolicy(enum.Enum):
    HARD_DELETE = 0
    SOFT_DELETE = 1


class PermissionActionName(enum.Enum):
    Add = "add"
    Change = "change"
    SoftDelete = "soft_delete"
    View = "view"
    List = "list"
    ViewTrash = "view_trash"
    Delete = "delete"
    Restore = "restore"
    Duplicate = "duplicate"
    Export = "export"
    Import = "import"
