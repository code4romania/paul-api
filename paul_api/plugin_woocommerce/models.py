from django.db import models
from django.contrib.auth.models import User

from api import models as api_models

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

    class Meta:
        pass


class TaskResult(api_models.PluginTaskResult):
    """
    Description: Model Description
    """
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.CASCADE,
        related_name='task_results')
