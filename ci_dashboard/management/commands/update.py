from django.core.management.base import BaseCommand
from ci_dashboard.tasks import synchronize


class Command(BaseCommand):
    help = 'Update CI status dashboard'

    def handle(self, *args, **options):
        synchronize.apply()
