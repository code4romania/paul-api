from rest_framework import serializers
from django.contrib.auth.models import User
from . import models


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


class OwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'first_name', 'last_name']


class TableDatabaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Database
        fields = ['url', 'name', 'slug']


class TableSerializer(serializers.HyperlinkedModelSerializer):
    database = TableDatabaseSerializer()
    owner = OwnerSerializer()

    class Meta:
        model = models.Table
        # fields = ['url', 'name']
        fields = '__all__'
        lookup_field = ['slug']


class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    tables = TableSerializer(many=True, read_only=True)

    class Meta:
        model = models.Database
        fields = ['url', 'name', 'tables']
