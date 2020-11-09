from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.dispatch import receiver
from django.db.models.signals import post_delete
from api import models as api_models

from django_celery_beat.models import CrontabSchedule, PeriodicTask

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

    periodic_task = models.ForeignKey(
        PeriodicTask, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='plugin_tasks')

    class Meta:
        pass

    @property
    def last_run_date(self):
        if self.task_results.exists():
            return self.task_results.order_by('-date_start').first().date_start
        else:
            return None


@receiver(post_delete, sender=Task)
def delete_periodic_task(sender, **kwargs):
    instance = kwargs.get('instance')
    instance.periodic_task.delete()

class TaskResult(api_models.PluginTaskResult):
    """
    Description: Model Description
    """
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.CASCADE,
        related_name='task_results')
