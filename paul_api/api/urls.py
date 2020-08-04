from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import routers
from . import views


# app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'databases', views.DatabaseViewSet)
router.register(r'tables', views.TableViewSet)

urlpatterns = [
    path('', include(router.urls))
]
