from django.contrib.auth.models import User

from api import models as api_models



from plugin_mailchimp import utils, models, serializers
from .table_fields import AUDIENCE_MEMBERS_FIELDS

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
    success = True
    stats = {
        'success': 0,
        'errors': 0,
        'errors_details': []
    }

    if hasattr(request, 'user'):
        user = request.user
    else:
        user, _ = User.objects.get_or_create(username='paul-sync')

    settings = models.Settings.objects.last()

    filtered_view = task.segmentation_task.filtered_view
    primary_table = filtered_view.primary_table

    audience_members_table = api_models.Table.objects.filter(name=settings.audience_members_table_name)

    if not audience_members_table.exists():
        success = False
        stats['errors'] += 1
        stats['errors_details'].append(
            '"{}" does not exists. Run mailchimp import task first.'.format(
                settings.audience_members_table_name
            ))
    else:
        audience_members_table = audience_members_table[0]
        if primary_table.table != audience_members_table:
            success = False
            stats['errors'] += 1
            stats['errors_details'].append(
                '"{}" needs to be the primary table in "{}" filtered view'.format(
                    audience_members_table, filtered_view.name
                ))
        primary_table_fields =  primary_table.fields.values_list('name', flat=True)
        mandatory_fields = ['audience_id', 'id', 'email_address']
        for field in mandatory_fields:
            if field not in primary_table_fields:
                success = False
                stats['errors'] += 1
                stats['errors_details'].append(
                    '"{}" field needs to be selected in the primary table in "{}" filtered view'.format(
                        AUDIENCE_MEMBERS_FIELDS[field]['display_name'], filtered_view.name
                    ))
        if success:
            lists_users = utils.get_emails_from_filtered_view(request, filtered_view, settings)
            success, stats = utils.add_list_to_segment(
                    settings,
                    lists_users,
                    task.segmentation_task.tag)

    task_result = models.TaskResult.objects.create(
        name="Segmentation",
        task=task,
        user=user,
        success=success,
        stats=stats)

    return task_result
