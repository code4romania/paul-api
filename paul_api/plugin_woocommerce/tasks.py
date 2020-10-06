from plugin_woocommerce import utils, models, serializers


def sync_wc(request):
    user = request.user
    settings = models.Settings.objects.last()

    KEY = settings.key
    SECRET = settings.secret
    ENDPOINT_URL = settings.endpoint_url

    success, updates, errors = utils.run_sync(ENDPOINT_URL, KEY, SECRET)

    task_result = models.TaskResult.objects.create(
        name="Sync tables",
        user=user,
        success=success,
        errors=errors,
        updates=updates)

    result = serializers.TaskResultSerializer(
        task_result, context={'request': request})

    return result.data
