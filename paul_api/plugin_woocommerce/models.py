from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

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


class TaskResult(models.Model):
    """
    Description: Model Description
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.CASCADE,
        related_name='task_results')
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name="woocommerce_tasks_results")
    success = models.BooleanField(default=False)
    stats = models.JSONField(
        encoder=DjangoJSONEncoder, null=True, blank=True)

    class Meta:
        ordering = ['-id']