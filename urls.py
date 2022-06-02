import sys

from django.urls import path

from lava.views import main_views


urlpatterns = [
    path('users/', main_views.user_list, name='user-list'),
    path('users/add', main_views.user_add, name='user-list'),
    path('users/<int:pk>/', main_views.user_details, name='user-detail'),
    path('users/<int:pk>/change', main_views.user_change, name='user-detail'),
    path('users/<int:pk>/change_pwd', main_views.user_change_pwd, name='user-change-pwd'),
]

if 'rest_framework' in sys.modules:
    from lava.views import api_views
    urlpatterns.extend([
        # path('', api_views.home),
        path('users/', api_views.UserListCreate.as_view(), name='user-list'),
        path('users/<int:pk>/', api_views.UserRetrieveUpdateDestroy.as_view(), name='user-detail'),
        path('users/<int:pk>/change_pwd', api_views.change_password, name='user-change-pwd'),
    ])
