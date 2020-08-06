from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework.authtoken import views as token_views

from . import views
from django.views.generic import TemplateView
# app_name = 'api'

router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"databases", views.DatabaseViewSet)
router.register(r"tables", views.TableViewSet)

urlpatterns = [
    path('api-token-auth/', token_views.obtain_auth_token),
    path('openapi', get_schema_view(
            title="Paul OpenSchema",
            description="API for Paul",
            version="0.0.1"
        ), name='openapi-schema'),
    path('swagger-ui/', TemplateView.as_view(
            template_name='api/swagger-ui.html',
            extra_context={'schema_url':'openapi-schema'}
        ), name='swagger-ui'),
    path("", include(router.urls))
]

