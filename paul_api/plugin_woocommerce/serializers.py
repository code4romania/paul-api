from django.urls import reverse
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


class TaskListSerializer(serializers.ModelSerializer):
    last_edit_user = OwnerSerializer(read_only=True)
    last_run_date = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="plugin_woocommerce:task-detail")

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


class TaskSerializer(serializers.ModelSerializer):
    last_edit_user = OwnerSerializer(read_only=True)
    task_results = serializers.SerializerMethodField()

    class Meta:
        model = models.Task
        fields = [
            "id",
            "name",
            "task_results",
            "task_type",
            "last_edit_date",
            "last_edit_user",
        ]

    def get_task_results(self, obj):
        return self.context["request"].build_absolute_uri(reverse("plugin_woocommerce:task-results-list", kwargs={"task_pk": obj.pk}))


class TaskCreateSerializer(serializers.ModelSerializer):
    last_edit_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Task
        fields = [
            "id",
            "name",
            "task_type",
            "last_edit_date",
            "last_edit_user",
        ]


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
            "status",
            "task",
            "date",
            "user",
            "success",
        ]

    def get_url(self, obj):
        return self.context["request"].build_absolute_uri(
            reverse(
                "plugin_woocommerce:task-results-detail",
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
            "status",
            "task",
            "date",
            "user",
            "success",
            "stats",
        ]