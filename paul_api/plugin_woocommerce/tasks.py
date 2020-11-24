from django.contrib.auth.models import User
from plugin_woocommerce import utils, models, serializers
from celery import shared_task


@shared_task
def sync(request, task_id):
    if hasattr(request, 'user'):
        user = request.user
    else:
        user, _ = User.objects.get_or_create(username='paul-sync')

    settings = models.Settings.objects.last()
    task = models.Task.objects.get(pk=task_id)

    task_result = models.TaskResult.objects.create(
        user=user,
        task=task)

    KEY = settings.key
    SECRET = settings.secret
    ENDPOINT_URL = settings.endpoint_url
    # TABLE_NAME = settings.table_name

    success, stats = utils.run_sync(ENDPOINT_URL, KEY, SECRET)

    task_result.success = success
    task_result.stats = stats
    task_result.status = 'Finished'
    task_result.save()

    return task_result.id, task_result.success
