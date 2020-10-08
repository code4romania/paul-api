from django.urls import reverse

from rest_framework import serializers

from api import models as api_models
from api.serializers.users import OwnerSerializer

from plugin_mailchimp import models

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
    last_run_date = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="plugin_mailchimp:task-detail")

    class Meta:
        model = models.Task
        fields = [
            "url",
            "id",
            "name",
            "task_type",
            "last_edit_date",
            "last_run_date",
            "last_edit_user",
        ]

    def get_last_run_date(self, obj):
        if obj.task_results.exists():
            return obj.task_results.last().date
        else:
            return None


class SegmentationTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SegmentationTask
        fields = [
            "filtered_view",
            # "email_field",
            # "audience_id",
            "tag",
        ]


class TaskSerializer(serializers.ModelSerializer):
    last_edit_user = OwnerSerializer(read_only=True)
    segmentation_task = SegmentationTaskSerializer()
    task_results = serializers.SerializerMethodField()

    class Meta:
        model = models.Task
        fields = [
            "id",
            "name",
            "task_results",
            "task_type",
            "segmentation_task",
            "last_edit_date",
            "last_edit_user",
        ]

    def get_task_results(self, obj):
        return self.context["request"].build_absolute_uri(reverse("plugin_mailchimp:task-results-list", kwargs={"task_pk": obj.pk}))


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
    url = serializers.SerializerMethodField()

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

    def get_url(self, obj):
        return self.context["request"].build_absolute_uri(
            reverse(
                "plugin_mailchimp:task-results-detail",
                kwargs={"pk": obj.pk, "task_pk": obj.task.pk},
            )
        )

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
