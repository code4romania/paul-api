from rest_framework import serializers
from api import models


class CsvImportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CsvImport
        fields = ["url", "table", "id",
                  "file", "errors_count", "imports_count"]


class CsvFieldMapSerializer(serializers.ModelSerializer):
    # field_type = serializers.SerializerMethodField()
    table_field = serializers.SerializerMethodField()

    class Meta:
        model = models.CsvFieldMap
        fields = ["original_name", "display_name", "field_type", "field_format", "table_field"]

    # def get_field_type(self, obj):
    #     print(obj)
    #     print(obj.field_type)
    #     return obj.field_type

    def get_table_field(self, obj):
        if obj.table_column:
            return obj.table_column.pk
        return None

class CsvImportSerializer(serializers.ModelSerializer):
    csv_field_mapping = CsvFieldMapSerializer(many=True)

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
            "csv_field_mapping",
        ]
