from django.urls import path

from rest_framework import routers

from lava.views import main_views, api_views


app_name = "lava"


router = routers.SimpleRouter()
router.register(r"notifications", api_views.NotificationViewSet)
router.register(r"preferences", api_views.PreferencesViewSet)


urlpatterns = [
    path("", main_views.home, name="home"),
    path(
        "users/activate/<str:uid>/<str:token>",
        main_views.activate_user,
        name="user-activate",
    ),
    path(
        "users/password/reset/confirm/<str:uid>/<str:token>",
        main_views.ResetPasswordConfirm.as_view(),
        name="user-reset-pwd-confirm",
    ),
    path(
        "users/update_device_id/",
        api_views.update_device_id,
        name="user-update-device-id",
    ),
    path("api/users/", api_views.UserListCreate.as_view(), name="user-list"),
    path(
        "api/users/<int:pk>/",
        api_views.UserRetrieveUpdateDestroy.as_view(),
        name="user-detail",
    ),
    path(
        "api/users/<int:pk>/change_pwd",
        api_views.change_password,
        name="user-change-pwd",
    ),
    path("api/maintenance", api_views.maintenance, name="maintenance"),
]

urlpatterns.extend(router.urls)
