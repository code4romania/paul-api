from django.urls import path, include
from django.contrib.auth.models import User

# from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework.authtoken import views as token_views

from rest_framework_nested import routers

from . import views
from django.views.generic import TemplateView

# app_name = 'api'

router = routers.DefaultRouter()

router.register(r"settings", views.SettingsViewSet)
router.register(r"task-results", views.TaskResultViewSet)

urlpatterns = [
    path("tasks/sync", views.RunSyncView.as_view()),
    path("", include(router.urls)),
]
