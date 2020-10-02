from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder


class Settings(models.Model):
    """
    Description: Model Description
    """
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    endpoint_url = models.URLField(max_length=255)

    class Meta:
        pass


class TaskResult(models.Model):
    """
    Description: Model Description
    """
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL)
    success = models.BooleanField(default=False)
    errors = models.JSONField(
        encoder=DjangoJSONEncoder, null=True, blank=True)
    updates = models.JSONField(
        encoder=DjangoJSONEncoder, null=True, blank=True)

    class Meta:
        pass
