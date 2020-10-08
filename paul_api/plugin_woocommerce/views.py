from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination

from plugin_woocommerce import (
    models,
    serializers,
    tasks)
from api.views import EntriesPagination


class TaskViewSet(viewsets.ModelViewSet):
    queryset = models.Task.objects.all()
    pagination_class = EntriesPagination

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.TaskListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return serializers.TaskCreateSerializer
        return serializers.TaskSerializer

    @action(
        detail=True,
        methods=["get"],
        name="Run Task",
        url_path="run",
    )
    def run(self, request, pk):
        task = self.get_object()
        print('*****')
        print('*****')
        print('*****')
        print('*****')
        print('*****')
        print('run')
        if task.task_type == 'sync':
            print('sync')
            task_result = tasks.sync(request)
            print('response')
            task_result.task = task
            task_result.save()

        result = serializers.TaskResultSerializer(
            task_result, context={'request': request})

        return Response(result.data)


class TaskResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.TaskResult.objects.all()
    pagination_class = EntriesPagination

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.TaskResultListSerializer
        return serializers.TaskResultSerializer

    def get_queryset(self):
        return models.TaskResult.objects.filter(task=self.kwargs["task_pk"])


class SettingsViewSet(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Settings.objects.all()
    serializer_class = serializers.SettingsSerializer



