import sys

from django.urls import path

from rest_framework import routers

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from lava import views


app_name = "lava"


api_router = routers.SimpleRouter()
activate_api_urls = "rest_framework" in sys.modules
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
        "users/",
        views.UserListView.as_view(),
        name="user-list",
    ),
]

if activate_api_urls:
    api_router.register(r"api/notifications", views.NotificationViewSet)
    api_router.register(r"api/notifications_groups", views.NotificationGroupViewSet)
    api_router.register(r"api/preferences", views.PreferencesViewSet)
    api_router.register(r"api/groups", views.GroupAPIViewSet)
    api_router.register(r"api/users", views.UserAPIViewSet)
    api_router.register(r"api/permissions", views.PermissionAPIViewSet)
    api_router.register(r"api/activity_journal", views.LogEntryAPIViewSet)
    api_router.register(r"api/backup", views.BackupAPIViewSet)
    api_router.register(r"api/chat", views.ChatAPIViewSet)
    api_router.register(
        r"api/dashboard", views.DashboardAPIViewSet, basename="dashboard"
    )
    api_router.register(r"api/banks", views.BankAPIViewSet)
    api_router.register(r"api/bank_accounts", views.BankAccountAPIViewSet)

    api_router.register(r"banks", views.BankAPIViewSet, basename="banks")
    api_router.register(
        r"bank_accounts", views.BankAccountAPIViewSet, basename="bankaccount"
    )

    api_urlpatterns = [
        # Swagger Documentation URLs
        path("api/schema", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs",
            SpectacularSwaggerView.as_view(
                url_name="lava:schema", template_name="lava/swagger_ui.html"
            ),
            name="swagger-ui",
        ),
        path(
            "api/docs/redoc",
            SpectacularRedocView.as_view(
                url_name="lava:schema",
            ),
            name="redoc-ui",
        ),
        path("api/choices/", views.ChoicesAPI.as_view(), name="api-choices"),
        path("api/users/me/", views.UserMeAPIView.as_view(), name="api-user-me"),
        path("api/settings/", views.SettingsListAPI.as_view(), name="api-settings"),
        path("api/maintenance/", views.maintenance, name="api-maintenance"),
        path(
            "api/auth_user_permissions/",
            views.get_user_permissions,
            name="api-get-user-permissions",
        ),
        path(
            "api/export_user_permissions/",
            views.ExportPermissions.as_view(),
            name="api-export-user-permissions",
        ),
        path(
            "api/export_activity_journal/",
            views.ExportActivityJournal.as_view(),
            name="api-export-activity-journal",
        ),
    ]

urlpatterns = [*base_urlpatterns, *api_urlpatterns, *api_router.urls]
