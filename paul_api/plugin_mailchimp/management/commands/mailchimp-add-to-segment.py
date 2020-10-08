from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import get_current_timezone, make_aware
from django.http import HttpRequest

from plugin_mailchimp import models, tasks, utils, serializers
from django.utils.text import slugify
from datetime import datetime, timedelta

from pprint import pprint



from rest_framework.request import Request
from rest_framework.test import force_authenticate, APIRequestFactory

from api import views
from django.test import RequestFactory

        


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print('add to segment mailchimp')

        # request = HttpRequest()
        # request.method = 'GET'
        # request.META['SERVER_NAME'] = 'dev.api.paul.ro'
        # request.META['SERVER_PORT'] = '8000'
        task = models.Task.objects.last()
        # view = views.FilterViewSet.as_view({'get': 'entries'})
        request = Request(request=HttpRequest())
        request = RequestFactory().request(HTTP_HOST='localhost:8001')
        print(request.user)
        # # Make an authenticated request to the view...
        # request = factory.get('/api/')
        # response = view(request)

        r = tasks.run_segmentation(request, task)
        # response = serializers.TaskResultSerializer(r, context={'request': request})
        # pprint(response.data)