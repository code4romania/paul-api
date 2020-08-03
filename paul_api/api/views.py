from django.shortcuts import render
from rest_framework import viewsets
from . import serializers, models
from django.contrib.auth.models import User


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = 'username'


class DatabaseViewSet(viewsets.ModelViewSet):
    queryset = models.Database.objects.all()
    serializer_class = serializers.DatabaseSerializer
    lookup_field = 'slug'


class TableViewSet(viewsets.ModelViewSet):
    queryset = models.Table.objects.all()
    serializer_class = serializers.TableSerializer
    lookup_field = 'slug'
