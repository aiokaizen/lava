from django.db import transaction
from lava.utils import Result


def atomic_transaction(func):
    def inner(*args, **kwargs):
        with transaction.atomic():
            result = func(*args, **kwargs)
            # Do something with result?
            # Don't forget to check if result is of the right type
            # ie: if type(result) == Result:
            return result

    return inner
