from plugin_woocommerce import utils, models, serializers


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

    success, stats = utils.run_sync(ENDPOINT_URL, KEY, SECRET)

    task_result.success=success
    task_result.stats=stats
    task_result.status = 'Finished'
    task_result.save()

    return task_result.id, task_result.success
