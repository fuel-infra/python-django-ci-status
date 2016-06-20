import os

from django.core.management.base import BaseCommand, CommandError
from ci_dashboard.models import CiSystem


class Command(BaseCommand):
    help = 'Import config from yaml file'

    def add_arguments(self, parser):
        parser.add_argument('config', nargs=1, type=str)

    def handle(self, *args, **options):
        config = options['config'][0]
        if os.path.exists(config):
            CiSystem.create_from_seed_file(config)
        else:
            raise CommandError("Config %s not found" % config)
