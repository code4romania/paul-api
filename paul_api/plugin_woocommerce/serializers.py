from rest_framework import serializers

from api.serializers.users import OwnerSerializer

from plugin_woocommerce import models


class SettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Settings
        fields = [
            "key",
            "secret",
            "endpoint_url",
        ]


class TaskResultListSerializer(serializers.ModelSerializer):
    user = OwnerSerializer(read_only=True)

    class Meta:
        model = models.TaskResult
        fields = [
            "url",
            "id",
            "date",
            "user",
            "success",
        ]


class TaskResultSerializer(serializers.ModelSerializer):
    user = OwnerSerializer(read_only=True)

    class Meta:
        model = models.TaskResult
        fields = [
            "id",
            "date",
            "user",
            "success",
            "updates",
            "errors"
        ]
