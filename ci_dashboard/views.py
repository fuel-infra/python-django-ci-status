import logging

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404

from ci_system.models import CiSystem, ProductCi


LOGGER = logging.getLogger(__name__)


def index(request):
    ci_systems = CiSystem.objects.filter(is_active=True).order_by('url')
    product_cis = ProductCi.objects.filter(is_active=True)
    number = 1
    versions = []
    for version_name, version_code in _all_versions_with_products():
        versions.append((number, version_name, version_code))
        number += 1

    context = {
        'product_cis': product_cis,
        'ci_systems_with_index': list(enumerate(ci_systems, start=2)),
        'versions': versions,
    }

    return render(request, 'ci_dashboard/index.html', context)


def ci_status_history(request, pk):
    ci = get_object_or_404(CiSystem, pk=pk)
    paginator = Paginator(ci.status_set.all(), 10)

    page = request.GET.get('page')
    try:
        statuses = paginator.page(page)
    except PageNotAnInteger:
        statuses = paginator.page(1)
    except EmptyPage:
        statuses = paginator.page(paginator.num_pages)

    return render(
        request,
        'ci_dashboard/ci_status_history.html',
        {'statuses': statuses, 'ci': ci}
    )


def dashboard(request):
    ci_systems = CiSystem.objects.filter(is_active=True).order_by('url')
    product_statuses = ProductCi.objects.filter(is_active=True)
    products_with_versions = []
    number = 1

    for pci in product_statuses:
        if pci.latest_rule_checks():
            products_with_versions.append((
                number,
                pci.version,
                pci.version.replace('.', '_'),
                pci,
                pci.current_status_type()
            ))
            number += 1

    statuses_summaries = [
        ci_system.latest_status()
        for ci_system in ci_systems
        if ci_system.latest_status()
    ]

    context = {
        'statuses_summaries': list(enumerate(statuses_summaries, 1)),
        'products_with_versions': products_with_versions,
    }

    return render(request, 'ci_dashboard/dashboard.html', context)


def _version_has_product_status(version):
    return any(
        pci for pci in ProductCi.objects.filter(
            is_active=True, version=version
        ) if pci.rules.filter(is_active=True)
    )


def _all_versions_with_products():
    return sorted(
        (version, version.replace('.', '_'))
        for version
        in ProductCi.objects.values_list('version', flat=True).distinct()
    )
