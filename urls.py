import sys

from django.urls import path

from rest_framework import routers

from lava import views


app_name = "lava"


api_router = routers.SimpleRouter()
activate_api_urls = 'rest_framework' in sys.modules
api_urlpatterns = []


base_urlpatterns = [
    path("", views.Home.as_view(), name="home"),
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.logout, name="logout"),
    path("signup/", views.Signup.as_view(), name="signup"),
    path("password_reset/", views.ResetPassword.as_view(), name="password_reset"),
    path("notifications/", views.Notifications.as_view(), name="notifications"),
    path(
        "users/activate/<str:uid>/<str:token>",
        views.activate_user,
        name="user-activate",
    ),
    path(
        "users/password/reset/confirm/<str:uid>/<str:token>",
        views.ResetPasswordConfirm.as_view(),
        name="user-reset-pwd-confirm",
    ),
    path(
        "users/update_device_id/",
        views.update_device_id,
        name="user-update-device-id",
    ),

    # User management urls
    path(
        "users/", views.UserListView.as_view(), name="user-list",
    ),
]

if activate_api_urls:
    api_router.register(r"api/notifications", views.NotificationViewSet)
    api_router.register(r"api/preferences", views.PreferencesViewSet)
    api_router.register(r"api/groups", views.GroupAPIViewSet)
    api_router.register(r"api/users", views.UserAPIViewSet)
    api_router.register(r"api/activity_journal", views.LogEntryAPIViewSet)

    api_urlpatterns = [
        path("api/maintenance", views.maintenance, name="api-maintenance"),
        path("api/auth_user_permissions", views.get_user_permissions, name="api-get-user-permissions"),
        path("api/export_user_permissions/", views.ExportPermissions.as_view() , name="api-export-user-permissions"),
        path("api/export_activity_journal/", views.ExportActivityJournal.as_view() , name="api-export-activity-journal"),
    ]

urlpatterns = [
    *base_urlpatterns,
    *api_urlpatterns,
    *api_router.urls
]
