from rest_framework import serializers
from api import models


class CsvImportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CsvImport
        fields = ["url", "table", "id",
                  "file", "errors_count", "imports_count"]


class CsvFieldMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CsvFieldMap
        fields = ["original_name", "field_name", "field_type", "field_format"]


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
