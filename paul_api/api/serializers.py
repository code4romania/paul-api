from rest_framework import serializers
from django.contrib.auth.models import User
from . import models


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']
        lookup_field = 'username'
        extra_kwargs = {
            'url': {'lookup_field': 'username'}
        }


class OwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'first_name', 'last_name']
        lookup_field = 'username'
        extra_kwargs = {
            'url': {'lookup_field': 'username'}
        }


class TableDatabaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Database
        fields = ['url', 'name', 'slug']
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class TableSerializer(serializers.HyperlinkedModelSerializer):
    database = TableDatabaseSerializer()
    owner = OwnerSerializer(read_only=True)
    last_edit_user = UserSerializer(read_only=True)
    # entries = 

    class Meta:
        model = models.Table
        lookup_field = 'slug'
        # fields = ['url', 'name']
        fields = '__all__'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'},
            'owner': {'lookup_field': 'username'},
            'database': {'lookup_field': 'slug'},
            'last_edit_user': {'lookup_field': 'username'},
        }


class DatabaseTableListSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    last_edit_user = OwnerSerializer()

    def get_entries(self, obj):
        return obj.entries.count()

    entries = serializers.SerializerMethodField()

    def get_queryset(self):
        print('qqq')

    class Meta:
        model = models.Table
        lookup_field = 'slug'
        fields = [
            'url',
            'name',
            'entries',
            'last_edit_date',
            'last_edit_user',
            'owner'
            ]
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'},
            'owner': {'lookup_field': 'username'},
            'last_edit_user': {'lookup_field': 'username'},
        }





class DatabaseSerializer(serializers.HyperlinkedModelSerializer):

    
    aa = DatabaseTableListSerializer(many=True, source='tables')

    class Meta:
        model = models.Database
        fields = ['url', 'name', 'aa', 'tables']
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'},
            'tables': {'lookup_field': 'slug'}
        }
