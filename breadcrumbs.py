from django.utils.translation import gettext as _


class Page:
    def __init__(self, title, label="", url="", parent=None, is_root=False):
        self.title = title
        self.label = ""
        self.is_root = is_root
        self.set_label(label)
        self.url = url
        self.set_parent(parent)

    def __str__(self):
        return self.label or self.title

    def set_label(self, label):
        self.label = label if label else self.title

    def set_parent(self, parent):
        self.parent = None
        if parent:  # parents is not None and len(parents) > 0
            if type(parent == self.__class__):
                self.parent = parent
            else:
                raise Exception(
                    "Parent has to be an instance of the class 'Page', not a '"
                    + str(parent.__class__)
                    + "' instance."
                )


def get_page_parents(page, depth=0):
    parents = []
    index = 0
    while page.parent is not None:
        parents.append(page.parent)
        page = page.parent
        if depth != 0:
            if index == depth:
                break
            index += 1
    parents.reverse()
    return parents


def get_page(breadcrumb_id):
    return breadcrumbs.get(breadcrumb_id, None)


# Define site structure
breadcrumbs = {
    "home": Page(title=_('Home - Lava'), label=_('Home'), is_root=True),
    "login": Page(title=_('Login - Lava'), label=_('Login'), is_root=True),
}

breadcrumbs['user_list'] = Page(title=_('Users'), label=_('Users'), parent=breadcrumbs['home'])
breadcrumbs['user_insert'] = Page(title=_('Create new user'), label=_('Create new user'), parent=breadcrumbs['user_list'])
breadcrumbs['user_details'] = Page(title=_('User Profile'), label=_('User profile'), parent=breadcrumbs['user_list'])
breadcrumbs['user_change'] = Page(title=_('Update Profile'), label=_('Update profile'), parent=breadcrumbs['user_details'])

breadcrumbs['group_list'] = Page(title=_('Groups'), label=_('Groups'), parent=breadcrumbs['home'])
breadcrumbs['group_insert'] = Page(title=_('Create new group'), label=_('Create new group'), parent=breadcrumbs['group_list'])
breadcrumbs['group_details'] = Page(title=_('Group details'), label=_('Group details'), parent=breadcrumbs['group_list'])
breadcrumbs['group_change'] = Page(title=_('Update group'), label=_('Update group'), parent=breadcrumbs['group_details'])

breadcrumbs['permissions_list'] = Page(title=_('Permissions'), label=_('Permissions'), parent=breadcrumbs['home'])
breadcrumbs['permissions_insert'] = Page(title=_('Create new permission'), label=_('Create new permission'), parent=breadcrumbs['permissions_list'])
breadcrumbs['permissions_details'] = Page(title=_('Permission details'), label=_('Permission details'), parent=breadcrumbs['permissions_list'])
breadcrumbs['permissions_change'] = Page(title=_('Update permission'), label=_('Update permission'), parent=breadcrumbs['permissions_details'])

breadcrumbs['logs'] = Page(title=_('Logs'), label=_('Permissions'), parent=breadcrumbs['home'])