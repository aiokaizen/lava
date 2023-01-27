from rest_framework.pagination import PageNumberPagination


class LavaPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    # page_size_query_description = _('Number of results to return per page.')
