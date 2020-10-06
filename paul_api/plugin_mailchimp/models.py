from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder


class Settings(models.Model):
    """
    Description: Model Description
    """
    key = models.CharField(max_length=255)
    audiences_table_name = models.CharField(max_length=255, default="[mailchimp] Audiences")
    audiences_stats_table_name = models.CharField(max_length=255, default="[mailchimp] Audiences Stats")
    audience_segments_table_name = models.CharField(max_length=255, default="[mailchimp] Audience Segments")
    audience_members_table_name = models.CharField(max_length=255, default="[mailchimp] Audiences Members")
    segment_members_table_name = models.CharField(max_length=255, default="[mailchimp] Segments Members")

    class Meta:
        pass


class TaskResult(models.Model):
    """
    Description: Model Description
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name="mailchimp_tasks")
    success = models.BooleanField(default=False)
    stats = models.JSONField(
        encoder=DjangoJSONEncoder, null=True, blank=True)
    class Meta:
        pass
