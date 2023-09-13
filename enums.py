import enum


class DeletePolicy(enum.Enum):
    HARD_DELETE = 0
    SOFT_DELETE = 1


class PermissionActionName(enum.Enum):
    List = "list"
    ListAll = "list_all"
    Choices = "choices"
    Add = "add"
    View = "view"
    Change = "change"
    Duplicate = "duplicate"
    SoftDelete = "soft_delete"
    ViewTrash = "view_trash"
    Restore = "restore"
    Delete = "delete"
    Import = "import"
    Export = "export"
