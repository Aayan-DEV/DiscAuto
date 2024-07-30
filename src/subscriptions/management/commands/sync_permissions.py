from typing import Any
from django.core.management.base import BaseCommand
from subscriptions.models import Subscription
from subscriptions import utils as subs_utils

class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        subs_utils.syc_subs_group_permissions()