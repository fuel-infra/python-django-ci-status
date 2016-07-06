import logging

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.contrib import messages

import json

from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django import forms

from ci_dashboard.models import CiSystem, ProductCi, Status, UserToken


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
    context = _dashboard_context(request)
    return render(request, 'ci_dashboard/dashboard.html', context)


def inline_dashboard(request):
    context = _dashboard_context(request)
    return render(request, 'ci_dashboard/inline_dashboard_panel.html', context)


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
        in ProductCi.objects.filter(is_active=True).values_list(
            'version', flat=True).distinct()
    )


def _dashboard_context(request):
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

    return {
        'statuses_summaries': list(enumerate(statuses_summaries, 1)),
        'products_with_versions': products_with_versions,
    }


@csrf_exempt
def import_file_json(request):
    if request.POST and request.FILES:
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                if user.is_staff and user.has_perm('ci_system.add_cisystem'):
                    return _import_file(request)
                else:
                    return _json_response(
                        status=401,
                        errors=[
                            'Authenticated user has not enough permissions.'
                        ])
            else:
                return _json_response(
                    status=401,
                    errors=['Authenticated user is disabled.'])
        else:
            return _json_response(
                status=403,
                errors=['Username or password is invalid.'])

    else:
        return _json_response(
            status=400,
            errors=[
                'For import you should make a POST request with file data '
                'and authentication credentials (username: password).'
            ])


def _import_file(request):
    seeds = CiSystem.parse_seeds_from_stream(
        request.FILES['file'].read()
    )

    if seeds:
        import_result = CiSystem.create_from_seeds(seeds)

        success_message_format = (
            '{cis_imported} of total {cis_total} Ci Systems and '
            '{ps_imported} of total {ps_total} Product Statuses '
            'were imported.'
        )

        success_message = success_message_format.format(
            cis_imported=import_result.get('cis_imported'),
            cis_total=import_result.get('cis_total'),
            ps_imported=import_result.get('ps_imported'),
            ps_total=import_result.get('ps_total')
        )

        return _json_response(
            status=200,
            data={
                'success_message': success_message,
                'error_messages': import_result.get('errors', [])
            })
    else:
        return _json_response(
            status=400,
            errors=[
                'Import file format is invalid.'
            ])


def _json_response(status=200, data={}, errors=[]):
    return HttpResponse(
        json.dumps({
            'status': status,
            'data': data,
            'errors': errors
        }),
        status=status,
        content_type='application/json')


class ImportFileForm(forms.Form):
    label = 'Select a YAML file'
    file = forms.FileField()


class StatusForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(StatusForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if not isinstance(self.fields[field], forms.BooleanField):
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })

    class Meta:
        model = Status
        fields = [
            'ci_system', 'status_type', 'summary', 'description', 'is_manual'
        ]


def status_detail(request, pk):
    status_detail = get_object_or_404(Status, pk=pk)

    context = {
        'status_detail': status_detail,
    }

    return render(request, 'status_detail.html', context)


@staff_member_required
@permission_required('ci_system.add_status', raise_exception=True)
def status_new(request, ci_id=None):
    form = StatusForm(request.POST or None,
                      initial={'is_manual': True, 'ci_system':  ci_id})
    context = {
        'csrf_token': csrf(request)['csrf_token'],
        'form': form,
        'form_action': reverse('status_new'),
    }

    if form.is_valid():
        status = form.save(commit=False)
        status.user = request.user
        status.last_changed_at = timezone.now()
        status.save()
        return redirect('status_detail', pk=status.pk)

    return render(request, 'status_new.html', context)


@staff_member_required
@permission_required('ci_system.change_status', raise_exception=True)
def status_edit(request, pk):
    status = get_object_or_404(Status, pk=pk)

    form = StatusForm(request.POST or None, instance=status)
    context = {
        'csrf_token': csrf(request)['csrf_token'],
        'form': form,
        'form_action': reverse('status_edit', kwargs={'pk': status.pk}),
    }

    if form.is_valid():
        status = form.save(commit=False)
        status.last_changed_at = timezone.now()
        status.user = request.user
        status.save()
        return redirect('status_detail', pk=status.pk)

    return render(request, 'status_edit.html', context)


@staff_member_required
@permission_required('ci_system.delete_status', raise_exception=True)
def status_delete(request, pk):
    status = get_object_or_404(Status, pk=pk)

    context = {
        'status': status,
        'csrf_token': csrf(request)['csrf_token'],
        'form_action': reverse('status_delete', kwargs={'pk': status.pk}),
    }

    if request.POST:
        status.delete()
        return redirect('ci_dashboard_index')

    return render(request, 'status_delete.html', context)


@csrf_exempt
@staff_member_required
@permission_required('ci_system.add_cisystem', raise_exception=True)
def import_file(request):
    is_json = request.META.get('HTTP_ACCEPT') == 'application/json'

    if request.method == 'POST' and request.FILES:
        form = ImportFileForm(request.POST, request.FILES)

        if form.is_valid():
            seeds = CiSystem.parse_seeds_from_stream(
                request.FILES['file'].read()
            )

            if seeds:
                import_result = CiSystem.create_from_seeds(seeds)

                success_message = (
                    '{cis_imported} of total {cis_total} Ci Systems and '
                    '{ps_imported} of total {ps_total} Product Statuses '
                    'were imported.'
                ).format(
                    cis_imported=import_result.get('cis_imported'),
                    cis_total=import_result.get('cis_total'),
                    ps_imported=import_result.get('ps_imported'),
                    ps_total=import_result.get('ps_total'),
                )

                messages.info(request, success_message)

                for error in import_result.get('errors', []):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        error
                    )

                if is_json:
                    return HttpResponse(json.dumps({
                        'status': 'ok',
                        'message': success_message,
                    }))
                return redirect('ci_dashboard_index')
            else:
                error_message = 'Import file format is invalid.'
                if is_json:
                    return HttpResponse(json.dumps({
                        'status': 'error',
                        'message': error_message,
                    }))
                messages.error(request, error_message)
                return render(request, 'import_file.html', {'form': form})
    else:
        form = ImportFileForm()

        return render(request, 'import_file.html', {'form': form})


@staff_member_required
@permission_required('ci_system.add_cisystem', raise_exception=True)
def generate_token(request):
    token, created = UserToken.objects.get_or_create(user=request.user)
    if not created and request.POST or not request.user.usertoken:
        token.token = ''
        token.save()
    return render(request, 'token.html', {'token': token.token})
