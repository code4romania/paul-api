from rest_framework import serializers
from django.contrib.auth.models import User
from django.urls import reverse
from . import models

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

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


class TableColumnSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TableColumn
        fields = ['name', 'field_type']


class TableDatabaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Database
        fields = ['url', 'name', 'slug']
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class TableSerializer(serializers.ModelSerializer):
    database = TableDatabaseSerializer()
    owner = OwnerSerializer(read_only=True)
    last_edit_user = UserSerializer(read_only=True)
    fields = TableColumnSerializer(many=True)
    entries = serializers.SerializerMethodField()

    class Meta:
        model = models.Table
        lookup_field = 'slug'
        fields = [
            'url',
            'database',
            'name',
            'slug',
            'owner',
            'last_edit_user',
            'last_edit_date',
            'date_created',
            'active',
            'fields',
            'entries'
            ]
        # fields = '__all__'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'},
            'owner': {'lookup_field': 'username'},
            'database': {'lookup_field': 'slug'},
            'last_edit_user': {'lookup_field': 'username'},
        }

    def get_entries(self, obj):
        return self.context['request'].build_absolute_uri(reverse('table-entries', kwargs={'slug': obj.slug}))


class DatabaseTableListSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    last_edit_user = OwnerSerializer()

    def get_entries(self, obj):
        return obj.entries.count()


    entries = serializers.SerializerMethodField()

    class Meta:
        model = models.Table
        lookup_field = 'slug'
        fields = [
            'url',
            'name',
            'active',
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
    active_tables = DatabaseTableListSerializer(many=True, read_only=True, context={'test': 'test'})
    archived_tables = DatabaseTableListSerializer(many=True, read_only=True,  context={'test': 'test'})

    class Meta:
        model = models.Database
        fields = ['url', 'name', 'active_tables', 'archived_tables',]
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'},
            'tables': {'lookup_field': 'slug'}
        }


class EntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Entry
        fields = ['date_created']

    def __init__(self, *args, **kwargs):
        fields = kwargs.get('context', {}).get('fields')
        # str_fields = request.GET.get('fields', '') if request else None
        # fields = str_fields.split(',') if str_fields else None

        super(EntrySerializer, self).__init__(*args, **kwargs)
        if fields is not None:
            for field_name in fields:
                print(self.fields)
                self.fields[field_name] = serializers.CharField(source='eav.{}'.format(field_name))

