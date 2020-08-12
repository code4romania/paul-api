from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import Group

from rest_framework import serializers
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

from . import models

from eav.models import Attribute

datatypes = {
    "int": Attribute.TYPE_INT,
    "float": Attribute.TYPE_FLOAT,
    "text": Attribute.TYPE_TEXT,
    "date": Attribute.TYPE_DATE,
    "bool": Attribute.TYPE_BOOLEAN,
    "object": Attribute.TYPE_OBJECT,
    "enum": Attribute.TYPE_ENUM,
}


def gen_slug(value):
    return slugify(value).replace("-", "_")


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
        fields = ["url", "username", "email", "is_staff"]
        lookup_field = "username"
        extra_kwargs = {"url": {"lookup_field": "username"}}


class OwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "first_name", "last_name"]
        lookup_field = "username"
        extra_kwargs = {"url": {"lookup_field": "username"}}


class TableColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TableColumn
        fields = ["name", "field_type"]


class TableDatabaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Database
        fields = ["url", "name", "slug"]
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}


class TableCreateSerializer(ObjectPermissionsAssignmentMixin, serializers.ModelSerializer):
    # database = TableDatabaseSerializer()
    database = serializers.SlugRelatedField(queryset=models.Database.objects.all(), slug_field='slug')
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    last_edit_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    last_edit_date = serializers.HiddenField(
        default=timezone.now()
    )
    active = serializers.HiddenField(
        default=True
    )
    fields = TableColumnSerializer(many=True)

    class Meta:
        model = models.Table
        # lookup_field = "slug"
        fields = [
            "database",
            "name",
            "owner",
            "fields",
            "last_edit_user",
            "last_edit_date",
            "active"
        ]
        extra_kwargs = {"database": {"lookup_field": "slug"}}

    def create(self, validated_data):
        print('validated_data', validated_data)
        temp_fields = validated_data.pop('fields')
        # database_slug = validated_data.pop('database')
        # database = models.Database.objects.get(slug=database_slug)
        # validated_data['database'] = database
        new_table = models.Table.objects.create(**validated_data)
        for i in temp_fields:
            models.TableColumn.objects.create(table=new_table, **i)
            Attribute.objects.get_or_create(
                    name=i['name'], slug=gen_slug(i['name']), datatype=datatypes[i['field_type']],
                )
        return new_table

    def get_permissions_map(self, created):
        current_user = self.context['request'].user
        print('current user', current_user)
        admins = Group.objects.get(name='admin')

        return {
            'view_table': [current_user, admins],
            'change_table': [current_user, admins],
            'delete_table': [current_user, admins]
        }

class TableSerializer(serializers.ModelSerializer):
    database = TableDatabaseSerializer()
    owner = OwnerSerializer(read_only=True)
    # owner = serializers.HiddenField(
    #     default=serializers.CurrentUserDefault()
    # )
    last_edit_user = UserSerializer(read_only=True)
    fields = TableColumnSerializer(many=True)
    entries = serializers.SerializerMethodField()

    class Meta:
        model = models.Table
        lookup_field = "slug"
        fields = [
            "url",
            "database",
            "name",
            "slug",
            "owner",
            "last_edit_user",
            "last_edit_date",
            "date_created",
            "active",
            "fields",
            "entries",
            "entries_count"
        ]
        # fields = '__all__'
        extra_kwargs = {
            "url": {"lookup_field": "slug"},
            "owner": {"lookup_field": "username"},
            "database": {"lookup_field": "slug"},
            "last_edit_user": {"lookup_field": "username"},
        }

    def get_entries(self, obj):
        return self.context["request"].build_absolute_uri(reverse("table-entries", kwargs={"slug": obj.slug}))


class DatabaseTableListSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    last_edit_user = OwnerSerializer()

    def get_entries(self, obj):
        return obj.entries.count()

    entries = serializers.SerializerMethodField()

    class Meta:
        model = models.Table
        lookup_field = "slug"
        fields = [
            "url",
            "name",
            "active",
            "entries",
            "last_edit_date",
            "last_edit_user",
            "owner",
        ]
        lookup_field = "slug"
        extra_kwargs = {
            "url": {"lookup_field": "slug"},
            "owner": {"lookup_field": "username"},
            "last_edit_user": {"lookup_field": "username"},
        }


class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    active_tables = DatabaseTableListSerializer(many=True, read_only=True)
    archived_tables = DatabaseTableListSerializer(many=True, read_only=True)

    class Meta:
        model = models.Database
        fields = [
            "url",
            "name",
            "active_tables",
            "archived_tables",
        ]
        lookup_field = "slug"
        extra_kwargs = {
            "url": {"lookup_field": "slug"},
            "tables": {"lookup_field": "slug"},
        }


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Entry
        fields = ["date_created"]

    def __init__(self, *args, **kwargs):
        fields = kwargs.get("context", {}).get("fields")
        # str_fields = request.GET.get('fields', '') if request else None
        # fields = str_fields.split(',') if str_fields else None

        super(EntrySerializer, self).__init__(*args, **kwargs)
        if fields is not None:
            for field_name in fields:
                self.fields[field_name] = serializers.CharField(source="eav.{}".format(field_name))
