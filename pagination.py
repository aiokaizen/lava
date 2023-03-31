from rest_framework.pagination import PageNumberPagination


class LavaPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    # page_size_query_description = _('Number of results to return per page.')

    def __init__(self, page_size=None):
        if page_size:
            self.page_size = page_size
        super().__init__()


def get_pagination_class(page_size):
    class PaginationClass(LavaPageNumberPagination):

        def __init__(self):
            super().__init__(page_size=page_size)

    return PaginationClass
