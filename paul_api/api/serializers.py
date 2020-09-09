from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import Group

from rest_framework import serializers
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

from . import models, utils

from datetime import datetime
from dateutil.parser import isoparse

from pprint import pprint

datatypes = {
    "int": "int",
    "float": "float",
    "text": "text",
    "date": "date",
    "bool": "bool",
    "enum": "enum",
}


DATATYPE_SERIALIZERS = {
    "text": serializers.CharField,
    "float": serializers.FloatField,
    "int": serializers.IntegerField,
    "date": serializers.DateTimeField,
    "bool": serializers.BooleanField,
    "enum": serializers.CharField,
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
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email"]

    def create(self, validated_data):
        new_user = User.objects.create(**validated_data)
        new_user.userprofile = models.Userprofile()
        new_user.save()
        userprofile = new_user.userprofile
        userprofile
        print("TODO: send mail")
        return new_user


class UserSerializer(serializers.HyperlinkedModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "url",
            "id",
            "username",
            "email",
            "avatar",
            "first_name",
            "last_name",
        ]

    def get_avatar(self, obj):
        try:
            request = self.context.get("request")
            avatar_url = obj.userprofile.avatar.url
            return request.build_absolute_uri(avatar_url)
        except:
            pass


class OwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "first_name", "last_name"]


class TableColumnSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    choices = serializers.SerializerMethodField()

    class Meta:
        model = models.TableColumn
        fields = [
            "id",
            "name",
            "display_name",
            "field_type",
            "help_text",
            "required",
            "unique",
            "choices",
        ]

    def get_choices(self, obj):
        if type(obj.choices) == list:
            return sorted(obj.choices)
        return []


class TableDatabaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Database
        fields = ["url", "id", "name", "slug"]


class TableCreateSerializer(
    ObjectPermissionsAssignmentMixin, serializers.ModelSerializer
):
    database = serializers.PrimaryKeyRelatedField(
        queryset=models.Database.objects.all()
    )
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    last_edit_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    last_edit_date = serializers.HiddenField(default=timezone.now())
    active = serializers.BooleanField(default=True)
    fields = TableColumnSerializer(many=True, required=False)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = models.Table
        fields = [
            "id",
            "database",
            "name",
            "owner",
            "fields",
            "last_edit_user",
            "last_edit_date",
            "active",
        ]

    def validate(self, data):
        if "id" in data.keys():
            table = models.Table.objects.get(pk=data["id"])
            if table.entries.exists():
                if "fields" in data.keys():
                    for field in data.get("fields"):
                        if "id" in field.keys():
                            field_obj = models.TableColumn.objects.get(
                                pk=field["id"]
                            )
                            if field_obj.field_type != field["field_type"]:
                                raise serializers.ValidationError(
                                    {
                                        "fields-{}".format(
                                            field["id"]
                                        ): "Changing field type is not permited on a table with entries"
                                    }
                                )
        return data

    def create(self, validated_data):
        temp_fields = []
        if "fields" in validated_data.keys():
            temp_fields = validated_data.pop("fields")

        new_table = models.Table.objects.create(**validated_data)
        for i in temp_fields:
            if "display_name" not in i.keys():
                i["display_name"] = i["name"]
                i["name"] = utils.snake_case(i["name"])
            if "name" not in i.keys():
                i["name"] = utils.snake_case(i["display_name"])

            models.TableColumn.objects.create(table=new_table, **i)

        return new_table

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.active = validated_data.get("active")
        instance.database = validated_data.get("database")
        instance.last_edit_user = self.context['request'].user

        if "fields" in validated_data.keys():
            # Check to see if we need to delete any field
            old_fields_ids = set(instance.fields.values_list("id", flat=True))
            new_fields_ids = set(
                [x.get("id") for x in validated_data.get("fields")]
            )
            for id_to_remove in old_fields_ids - new_fields_ids:
                field = models.TableColumn.objects.get(pk=id_to_remove)
                field_name = field.name
                field.delete()
                for entry in instance.entries.all():
                    del entry.data[field_name]
                    entry.save()
            # Create or update fields
            for field in validated_data.pop("fields"):
                if "id" in field.keys():
                    field_obj = models.TableColumn.objects.get(pk=field["id"])
                    old_name = field_obj.name
                    new_name = field["name"]
                    if old_name != new_name:

                        for entry in instance.entries.all():
                            entry.data[new_name] = entry.data[old_name]
                            del entry.data[old_name]
                            entry.save()
                    field_obj.__dict__.update(field)
                    field_obj.save()
                else:
                    field["table"] = instance
                    field['name'] = utils.snake_case(field['display_name'])
                    pprint(field)
                    models.TableColumn.objects.create(**field)

        instance.save()
        return instance

    def get_permissions_map(self, created):
        current_user = self.context["request"].user
        admins = Group.objects.get(name="admin")

        return {
            "view_table": [current_user, admins],
            "change_table": [current_user, admins],
            "delete_table": [current_user, admins],
        }


class TableSerializer(serializers.ModelSerializer):
    database = TableDatabaseSerializer()
    owner = OwnerSerializer(read_only=True)
    last_edit_user = UserSerializer(read_only=True)
    fields = TableColumnSerializer(many=True)
    entries = serializers.SerializerMethodField()
    default_fields = serializers.SerializerMethodField()

    class Meta:
        model = models.Table
        fields = [
            "url",
            "id",
            "name",
            "entries",
            "entries_count",
            "database",
            "slug",
            "owner",
            "last_edit_user",
            "last_edit_date",
            "date_created",
            "active",
            "default_fields",
            "fields",
        ]

    def get_default_fields(self, obj):
        return [
            x for x in obj.fields.values_list("name", flat=True).order_by("id")
        ][:7]

    def get_entries(self, obj):
        return self.context["request"].build_absolute_uri(
            reverse("table-entries-list", kwargs={"table_pk": obj.pk})
        )


class DatabaseTableListDataSerializer(serializers.ModelSerializer):
    entries = serializers.SerializerMethodField()
    # last_edit_user = serializers.ReadOnlyField(source='last_edit_user.userprofile.full_name')
    last_edit_user = OwnerSerializer()
    def get_entries(self, obj):
        return obj.entries.count()

    class Meta:
        model = models.Table
        fields = [
            "name",
            "entries",
            "last_edit_date",
            "last_edit_user",
        ]


class DatabaseTableListSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    data = serializers.SerializerMethodField()

    def get_data(self, obj):
        serializer = DatabaseTableListDataSerializer(obj, context=self.context)
        return serializer.data

    class Meta:
        model = models.Table
        fields = ["url", "id", "active", "owner", "data"]


class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    active_tables = DatabaseTableListSerializer(many=True, read_only=True)
    archived_tables = DatabaseTableListSerializer(many=True, read_only=True)

    class Meta:
        model = models.Database
        fields = [
            "url",
            "id",
            "name",
            "active_tables",
            "archived_tables",
        ]


class EntryDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Entry
        fields = []

    def __init__(self, *args, **kwargs):
        fields = kwargs.get("context", {}).get("fields")
        table = kwargs.get("context", {}).get("table")

        if table:
            table_fields = {field.name: field for field in table.fields.all()}

        super(EntryDataSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            for field_name in fields:
                MappedField = DATATYPE_SERIALIZERS[
                    table_fields[field_name].field_type
                ]
                self.fields[field_name] = MappedField(
                    source="data.{}".format(field_name), required=False
                )


class EntrySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = models.Entry
        fields = ["url", "id", "date_created", "data"]

    def validate(self, attrs):
        table = self.context.get("table")
        table_fields = {field.name: field for field in table.fields.all()}
        errors = {}

        unknown = (
            set(self.initial_data) - set(self.fields) - set(table_fields.keys())
        )

        if unknown:
            errors["non_field_errors"] = "Unknown field(s): {}".format(
                ", ".join(unknown)
            )

        for field_name, field_value in self.initial_data.items():
            if field_name in table_fields.keys():
                field = table_fields[field_name]

                if field.field_type == "int":
                    try:
                        int(field_value)
                    except:
                        errors[field_name] = "Integer is not valid"
                elif field.field_type == "float":
                    try:
                        float(field_value)
                    except:
                        errors[field_name] = "Float is not valid"
                elif field.field_type == "date":
                    try:
                        # datetime.strptime(field_value, "%Y-%m-%dT%H:%M:%S%z")
                        isoparse(field_value)
                    except Exception as e:
                        print(e)
                        errors[field_name] = "Invalid date format"
                elif field.field_type == "enum":
                    if field_value not in field.choices:
                        errors[
                            field_name
                        ] = "{} is not a valid choice({})".format(
                            field_value, ",".join(field.choices)
                        )

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def get_data(self, obj):
        serializer = EntryDataSerializer(obj, context=self.context)
        return serializer.data

    def __init__(self, *args, **kwargs):
        fields = kwargs.get("context", {}).get("fields")
        table = kwargs.get("context", {}).get("table")

        super(EntrySerializer, self).__init__(*args, **kwargs)

        self.fields["data"].context.update({"table": table, "fields": fields})

    def create(self, validated_data):
        validated_data["data"] = self.initial_data
        validated_data["table"] = self.context["table"]
        instance = models.Entry.objects.create(**validated_data)
        instance.table.last_edit_user = self.context['request'].user
        instance.table.last_edit_date = datetime.now()
        instance.table.save()
        return instance

    def update(self, instance, validated_data, *args, **kwargs):
        instance.data = self.initial_data
        instance.table.last_edit_user = self.context['request'].user
        instance.table.last_edit_date = datetime.now()
        instance.table.save()
        instance.save()
        return instance

    def get_url(self, obj):
        return self.context["request"].build_absolute_uri(
            reverse(
                "table-entries-detail",
                kwargs={"pk": obj.pk, "table_pk": obj.table.pk},
            )
        )


class FilterEntrySerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.get("context", {}).get("fields")

        super(FilterEntrySerializer, self).__init__(*args, **kwargs)
        if fields is not None:
            for field_name in fields:
                # MappedField = DATATYPE_SERIALIZERS[table_fields[field_name].field_type]
                try:
                    self.fields[field_name] = serializers.CharField()
                except:
                    pass


class FilterListDataSerializer(serializers.ModelSerializer):
    tables = serializers.SerializerMethodField()
    show_in_dashboard = serializers.SerializerMethodField()
    owner = OwnerSerializer()

    def get_show_in_dashboard(self, obj):
        userprofile = self.context["request"].user.userprofile
        return obj in userprofile.dashboard_filters.all()

    def get_tables(self, obj):
        if obj.primary_table:
            tables = [obj.primary_table.table.name] + list(
                obj.join_tables.values_list("table__name", flat=True)
            )
            return tables
        return "-"

    class Meta:
        model = models.Filter
        fields = [
            "name",
            "creation_date",
            "tables",
            "owner",
            "show_in_dashboard",
        ]


class FilterListSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    def get_data(self, obj):
        serializer = FilterListDataSerializer(obj, context=self.context)
        return serializer.data

    class Meta:
        model = models.Filter
        fields = ["url", "id", "data"]


class FilterJoinTableListSerializer(serializers.ModelSerializer):
    table = serializers.SerializerMethodField()
    join_field = serializers.SerializerMethodField()
    fields = TableColumnSerializer(many=True)

    class Meta:
        model = models.FilterJoinTable
        fields = ["table", "join_field", "fields"]

    def get_table(self, obj):
        return obj.table.name

    def get_join_field(self, obj):
        return obj.join_field.name


class FilterDetailSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    last_edit_user = OwnerSerializer()

    entries = serializers.SerializerMethodField()
    config = serializers.SerializerMethodField()
    fields = serializers.SerializerMethodField(method_name='get_filter_fields')
    default_fields = serializers.SerializerMethodField()

    class Meta:
        model = models.Filter
        fields = [
            "url",
            "id",
            "name",
            "entries",
            "owner",
            "last_edit_user",
            "last_edit_date",
            "config",
            "fields",
            "default_fields",
            "filters"
        ]

    def get_filter_fields(self, obj):
        fields = []
        primary_table = obj.primary_table
        secondary_table = obj.join_tables.all()[0]

        for field in primary_table.fields.all():
            fields.append({
                "id": field.id,
                "table_id": primary_table.id,
                "name": "{}__{}".format(primary_table.table.slug, field.name),
                "display_name": field.display_name,
                "field_type": field.field_type,
                "choices": field.choices
                })
        for field in secondary_table.fields.all():
            fields.append({
                "id": field.id,
                "table_id": secondary_table.id,
                "name": "{}__{}".format(secondary_table.table.slug, field.name),
                "display_name": field.display_name,
                "field_type": field.field_type,
                "choices": field.choices
                })
        return fields

    def get_default_fields(self, obj):
        primary_table = obj.primary_table
        secondary_table = obj.join_tables.all()[0]
        all_fields = ['{}__{}'.format(primary_table.table.slug, x.name) for x in primary_table.fields.all().order_by('id')]
        all_fields += ['{}__{}'.format(secondary_table.table.slug, x.name) for x in secondary_table.fields.all().order_by('id')]

        return all_fields[:7]

    def get_config(self, obj):
        serializer = FilterCreateSerializer(obj, context=self.context)
        return serializer.data


    def get_entries(self, obj):
        return self.context["request"].build_absolute_uri(
            reverse("filter-entries", kwargs={"pk": obj.pk})
        )


class FilterJoinTableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FilterJoinTable
        fields = ["table", "fields", "join_field"]


class FilterCreateSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    last_edit_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    last_edit_date = serializers.HiddenField(default=timezone.now())
    primary_table = FilterJoinTableCreateSerializer()
    join_tables = FilterJoinTableCreateSerializer(many=True)

    class Meta:
        model = models.Filter
        fields = [
            "id",
            "name",
            "owner",
            "last_edit_user",
            "last_edit_date",
            "primary_table",
            "join_tables",
            "filters"
        ]

    def create(self, validated_data):
        primary_table = validated_data.pop("primary_table")
        join_tables = validated_data.pop("join_tables")

        new_filter = models.Filter.objects.create(**validated_data)

        fields = primary_table.pop("fields")
        primary_table = models.FilterJoinTable.objects.create(**primary_table)
        primary_table.fields.set(fields)

        new_filter.primary_table = primary_table
        new_filter.save()

        for join_table in join_tables:
            fields = join_table.pop("fields")
            join_table = models.FilterJoinTable.objects.create(**join_table)
            join_table.fields.set(fields)

            new_filter.join_tables.add(join_table)
        return new_filter

    def update(self, instance, validated_data):
        if self.partial:
            models.Filter.objects.filter(pk=instance.pk).update(**validated_data)
        else:
            instance.name = validated_data.get("name")
            instance.last_edit_user = self.request.user
            print(instance.last_edit_user)
            instance.filters = validated_data.get("filters")
            primary_table_data = validated_data.pop("primary_table")
            join_tables = validated_data.pop("join_tables")


            primary_table = instance.primary_table
            primary_table.table = primary_table_data["table"]
            primary_table.join_field = primary_table_data["join_field"]
            primary_table.fields.set(primary_table_data["fields"])
            primary_table.save()

            instance.join_tables.set([])
            for table in instance.join_tables.all():
                table.delete()
            for join_table in join_tables:
                fields = join_table.pop("fields")
                join_table = models.FilterJoinTable.objects.create(**join_table)
                join_table.fields.set(fields)

                instance.join_tables.add(join_table)
            instance.save()
        return instance


class CsvImportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CsvImport
        fields = ["url", "table", "id", "file", "errors_count", "imports_count"]


class CsvImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CsvImport
        fields = [
            "url",
            "table",
            "id",
            "file",
            "delimiter",
            "errors_count",
            "imports_count",
            "errors",
        ]
