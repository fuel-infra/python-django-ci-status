# flake8: noqa

from __future__ import unicode_literals

import logging

from django.db import models

LOGGER = logging.getLogger(__name__)


class Stats(models.Model):

    name = models.CharField(max_length=255, unique=True)
    updated_at = models.DateTimeField(auto_now=True)


def update_last_sync_timestamp():
    last_sync, created = Stats.objects.get_or_create(name='last_sync')
    last_sync.save()
