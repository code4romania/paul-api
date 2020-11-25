from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import get_current_timezone, make_aware
from django.http import HttpRequest

from plugin_woocommerce import utils
from django.utils.text import slugify
from datetime import datetime, timedelta

from pprint import pprint

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print('sync mailchimp')
        KEY= '123'
        SECRET = 'asdasd'
        ENDPOINT_URL = 'http://endpoint'
        print(utils.main(
            KEY,
            SECRET,
            ENDPOINT_URL
            ))