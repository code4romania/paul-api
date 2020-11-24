from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_delete

from api import models as api_models

from django_celery_beat.models import CrontabSchedule, PeriodicTask
TASK_TYPES = (
    ('sync', 'Import tables'),
    )


class Settings(models.Model):
    """
    Description: Model Description
    """
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    endpoint_url = models.URLField(max_length=255)

    class Meta:
        pass


class Task(models.Model):
    """
    Description: Model Description
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    task_type = models.CharField(max_length=100, choices=TASK_TYPES)

    last_edit_date = models.DateTimeField(auto_now=True)
    last_edit_user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name="woocommerce_tasks")

    periodic_task = models.ForeignKey(
        PeriodicTask, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='woocommerce_tasks')

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
    if instance.periodic_task:
        instance.periodic_task.delete()


class TaskResult(api_models.PluginTaskResult):
    """
    Description: Model Description
    """
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.CASCADE,
        related_name='task_results')
