import sys


from .main_views import *

if "rest_framework" in sys.modules:
    from .api_views import *
