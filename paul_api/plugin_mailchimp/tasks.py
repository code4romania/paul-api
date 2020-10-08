from django.contrib.auth.models import User

from plugin_mailchimp import utils, models, serializers


def sync(request):
    if hasattr(request, 'user'):
        user = request.user
    else:
        user, _ = User.objects.get_or_create(username='paul-sync')
    settings = models.Settings.objects.last()

    KEY = settings.key
    AUDIENCES_TABLE_NAME = settings.audiences_table_name
    AUDIENCES_STATS_TABLE_NAME = settings.audiences_stats_table_name
    AUDIENCE_MEMBERS_TABLE_NAME = settings.audience_members_table_name
    AUDIENCE_SEGMENTS_TABLE_NAME = settings.audience_segments_table_name
    SEGMENT_MEMBERS_TABLE_NAME = settings.segment_members_table_name
    AUDIENCE_TAGS_TABLE_NAME = settings.audience_tags_table_name

    success, stats = utils.run_sync(
        KEY,
        AUDIENCES_TABLE_NAME,
        AUDIENCES_STATS_TABLE_NAME,
        AUDIENCE_SEGMENTS_TABLE_NAME,
        AUDIENCE_MEMBERS_TABLE_NAME,
        SEGMENT_MEMBERS_TABLE_NAME,
        AUDIENCE_TAGS_TABLE_NAME
    )

    task_result = models.TaskResult.objects.create(
        name="Sync audiences",
        user=user,
        success=success,
        stats=stats)

    return task_result


def run_segmentation(request, task):
    if hasattr(request, 'user'):
        user = request.user
    else:
        user, _ = User.objects.get_or_create(username='paul-sync')
    settings = models.Settings.objects.last()
    emails = ['costin.bleotu@code.ro']
    success, stats = utils.add_list_to_segment(
            settings,
            emails,
            task.segmentation_task.audience_id,
            task.segmentation_task.tag)

    task_result = models.TaskResult.objects.create(
        name="Segmentation",
        task=task,
        user=user,
        success=success,
        stats=stats)

    return task_result
