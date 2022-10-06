from django import template

from lava import settings as lava_settings
from lava.breadcrumbs import get_page, get_page_parents as get_parents

register = template.Library()


def in_range(current, index, range):
    max = current + range
    min = current - range

    if index > max or index < min:
        return False
    return True


@register.filter()
def in_range_2(current, index):
    return in_range(current, index, 2)


@register.filter("get_page")
def get_page_from_id(breadcrumb_id):
    page = get_page(breadcrumb_id)
    return page


@register.filter()
def get_breadcrumbs(breadcrumb_id, path):
    page = get_page(breadcrumb_id)
    # depth = lava_settings.BREADCRUMBS_DEPTH_LEVEL
    if page:
        parents = get_parents(page)
        index = 0
        parent_url = ""
        # if len(parents) > depth:
        #     index = len(parents) - depth
        #     parent_url = '/'
        #     parents = parents[-depth:]
        path_fragments = path.split("/")
        for parent in parents:
            parent_url += path_fragments[index] + "/"
            parent.url = parent_url
            index += 1
        return parents, page.label

    return [], breadcrumb_id
