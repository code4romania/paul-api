from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

from api import models as api_models

TASK_TYPES = (
    ('sync', 'Import tables'),
    ('segmentation', 'Send segmentation')
    )


class Settings(models.Model):
    """
    Description: Model Description
    """
    key = models.CharField(max_length=255)
    audiences_table_name = models.CharField(
        max_length=255, default="[mailchimp] Audiences")
    audiences_stats_table_name = models.CharField(
        max_length=255, default="[mailchimp] Audiences Stats")
    audience_segments_table_name = models.CharField(
        max_length=255, default="[mailchimp] Audience Segments")
    audience_members_table_name = models.CharField(
        max_length=255, default="[mailchimp] Audiences Members")
    segment_members_table_name = models.CharField(
        max_length=255, default="[mailchimp] Segments Members")
    audience_tags_table_name = models.CharField(
        max_length=255, default="[mailchimp] Audience Tags")

    class Meta:
        pass


class SegmentationTask(models.Model):
    """
    Description: Model Description
    """
    filtered_view = models.ForeignKey(
        api_models.Filter, null=True, blank=True,
        on_delete=models.CASCADE)
    # email_field = models.CharField(max_length=100, null=True, blank=True)
    # audience_id = models.CharField(max_length=100, null=True, blank=True)
    tag = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        pass


class Task(models.Model):
    """
    Description: Model Description
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    task_type = models.CharField(max_length=100, choices=TASK_TYPES)

    segmentation_task = models.ForeignKey(
        SegmentationTask, null=True, blank=True, on_delete=models.CASCADE)

    last_edit_date = models.DateTimeField(auto_now=True)
    last_edit_user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name="mailchimp_tasks")

    class Meta:
        pass


class TaskResult(models.Model):
    """
    Description: Model Description
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, default='In progress')
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.CASCADE,
        related_name='task_results')
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name="mailchimp_tasks_results")
    success = models.BooleanField(default=False)
    stats = models.JSONField(
        encoder=DjangoJSONEncoder, null=True, blank=True)

    class Meta:
        ordering = ['-id']
