from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from subscriptions import utils as subs_utils
from customers.models import Customer
import helpers.billing

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--clear-dangling", action="store_true", default=False)

    def handle(self, *args: Any, **options: Any):
        clear_dangling = options.get("clear_dangling")
        if clear_dangling:
            print("Clearing dangling subscriptions...")
            subs_utils.clear_dangling_subs()
        else:
            print("Sync active subscriptions.")
            print("Done.")
            
            
