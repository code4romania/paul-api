from django.urls import path, include

from rest_framework_nested import routers

from . import views

# app_name = 'plugin_woocommerce'

router = routers.DefaultRouter()

router.register(r"settings", views.SettingsViewSet)
router.register(r"task-results", views.TaskResultViewSet)

urlpatterns = [
    path("tasks/sync", views.RunSyncView.as_view()),
    path("", include(router.urls)),
]