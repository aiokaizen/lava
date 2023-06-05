from django.db import connection


def execute_query(klass, query, params=[]):
    """
        klass: The class or queryset that is used to retrieve items eg: User
        query: SQL query that must return a list of ids. eg: SELECT id FROM ... WHERE ...
        params: list of parameters to pass to the query
    """
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        ids = [row[0] for row in cursor.fetchall()]
        if hasattr(klass, 'objects'):
            return klass.objects.filter(id__in=ids)
        return klass.filter(id__in=ids)
