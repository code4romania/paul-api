from rest_framework import serializers

from api.serializers.users import OwnerSerializer

from plugin_mailchimp import models
from api import models as api_models

from pprint import pprint


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
            "audience_tags_table_name",
        ]


class TaskListSerializer(serializers.ModelSerializer):
    last_edit_user = OwnerSerializer(read_only=True)

    class Meta:
        model = models.Task
        fields = [
            "url",
            "id",
            "name",
            "task_type",
            "last_edit_date",
            "last_edit_user",
        ]


class SegmentationTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SegmentationTask
        fields = [
            "filtered_view",
            "email_field",
            "audience_id",
            "tag",
        ]


class TaskSerializer(serializers.ModelSerializer):
    last_edit_user = OwnerSerializer(read_only=True)
    segmentation_task = SegmentationTaskSerializer()

    class Meta:
        model = models.Task
        fields = [
            "id",
            "name",
            "task_type",
            "segmentation_task",
            "last_edit_date",
            "last_edit_user",
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    last_edit_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault())
    segmentation_task = SegmentationTaskSerializer()

    class Meta:
        model = models.Task
        fields = [
            "id",
            "name",
            "task_type",
            "segmentation_task",
            "last_edit_date",
            "last_edit_user",
        ]

    def create(self, validated_data):
        task_type = validated_data['task_type']
        segment_data = validated_data.pop('segmentation_task')
        if task_type == 'segmentation':
            segmentation_task = models.SegmentationTask.objects.create(
                **segment_data)

        task = models.Task.objects.create(**validated_data)
        if task_type == 'segmentation':
            task.segmentation_task = segmentation_task
            task.save()
        return task


class TaskResultListSerializer(serializers.ModelSerializer):
    user = OwnerSerializer(read_only=True)
    task = serializers.ReadOnlyField(source='task.name')

    class Meta:
        model = models.TaskResult
        fields = [
            "url",
            "id",
            "name",
            "task",
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
            "task",
            "date",
            "user",
            "success",
            "stats",
        ]
