from rest_framework import serializers
from api import models
from django.urls import reverse
from datetime import datetime
from dateutil.parser import isoparse

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

        entry = args[0]
        # print(kwargs)
        if fields is not None:
            for field_name in fields:
                MappedField = DATATYPE_SERIALIZERS[table_fields[field_name].field_type]
                if field_name in args[0].data.keys() and args[0].data[field_name] != '':
                    self.fields[field_name] = MappedField(source="data.{}".format(field_name), required=False)


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

        unknown = set(self.initial_data) - set(self.fields) - set(table_fields.keys())

        if unknown:
            errors["non_field_errors"] = "Unknown field(s): {}".format(", ".join(unknown))

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
                        errors[field_name] = "{} is not a valid choice({})".format(
                            field_value, ",".join(field.choices))

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
        instance.table.last_edit_user = self.context["request"].user
        instance.table.last_edit_date = datetime.now()
        instance.table.save()
        return instance

    def update(self, instance, validated_data, *args, **kwargs):
        instance.data = self.initial_data
        instance.table.last_edit_user = self.context["request"].user
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
