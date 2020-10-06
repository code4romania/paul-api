from rest_framework import serializers

from api.serializers.users import OwnerSerializer

from plugin_mailchimp import models


class SettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Settings
        fields = [
            "key",
            "audiences_table_name",
            "audiences_stats_table_name",
            "audience_segments_table_name",
            "audience_members_table_name",
            "segment_members_table_name",
        ]


class TaskResultListSerializer(serializers.ModelSerializer):
    user = OwnerSerializer(read_only=True)

    class Meta:
        model = models.TaskResult
        fields = [
            "url",
            "id",
            "name",
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
            "name",
            "date",
            "user",
            "success",
            "stats",
        ]
