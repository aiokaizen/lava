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
breadcrumbs = {"home": Page(title="Home - Lava", label="Home", is_root=True)}

# breadcrumbs['profile_details'] = Page(title='Profile', label='Profile', parent=breadcrumbs['home'])
# breadcrumbs['profile_change'] = Page(title='Update Profile', label='Update profile', parent=breadcrumbs['profile_details'])

# breadcrumbs['invoice_list'] = Page(title='Invoices', label='Invoices', parent=breadcrumbs['home'])
# breadcrumbs['invoice_add'] = Page(title='New Invoice', label='New invoice', parent=breadcrumbs['invoice_list'])
# breadcrumbs['invoice_details'] = Page(title='Invoice details', label='Invoice details', parent=breadcrumbs['invoice_list'])
# breadcrumbs['invoice_change'] = Page(title='Update Invoice', label='Update invoice', parent=breadcrumbs['invoice_details'])
