import sys

from django.urls import path

from lava.views import main_views


urlpatterns = [
    path('', main_views.home),
    path('users/', main_views.user_list, name='user-list'),
    path('users/add', main_views.user_add, name='user-add'),
    path('users/activate/<str:uid>/<str:token>', main_views.activate_user, name='user-activate'),
    path('users/password/reset/confirm/<str:uid>/<str:token>', main_views.reset_pwd_confirm, name='user-reset-pwd-confirm'),
    path('users/<int:pk>/', main_views.user_details, name='user-detail'),
    path('users/<int:pk>/change', main_views.user_change, name='user-change'),
    path('users/<int:pk>/change_pwd', main_views.user_change_pwd, name='user-change-pwd'),
]

if 'rest_framework' in sys.modules:
    from lava.views import api_views
    urlpatterns.extend([
        path('api/users/', api_views.UserListCreate.as_view(), name='api-user-list'),
        path('api/users/<int:pk>/', api_views.UserRetrieveUpdateDestroy.as_view(), name='api-user-detail'),
        path('api/users/<int:pk>/change_pwd', api_views.change_password, name='api-user-change-pwd'),
    ])
