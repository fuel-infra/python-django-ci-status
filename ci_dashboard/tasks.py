from __future__ import absolute_import

import logging
from celery import shared_task

from ci_system.models import CiSystem, ProductCi
from ci_dashboard.models import update_last_sync_timestamp


LOGGER = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def synchronize():
    _update_cis()
    _update_product_cis()
    update_last_sync_timestamp()


def _update_cis():
    ci_systems = CiSystem.objects.filter(is_active=True)

    for ci in ci_systems:
        ci.check_the_status()


def _update_product_cis():
    products = ProductCi.objects.filter(is_active=True)

    for pci in products:
        pci.set_status()
