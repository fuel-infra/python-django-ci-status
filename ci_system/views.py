import logging

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.shortcuts import redirect, render, get_object_or_404

from ci_system.models import Status, CiSystem


LOGGER = logging.getLogger(__name__)


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


@staff_member_required
@permission_required('ci_system.add_cisystem', raise_exception=True)
def import_file(request):
    if request.POST and request.FILES:
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
                )

                messages.info(request, success_message.format(
                    cis_imported=import_result.get('cis_imported'),
                    cis_total=import_result.get('cis_total'),
                    ps_imported=import_result.get('ps_imported'),
                    ps_total=import_result.get('ps_total'),
                ))

                for error in import_result.get('errors', []):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        error
                    )

                return redirect('ci_dashboard_index')
            else:
                messages.error(request, 'Import file format is invalid.')
                return render(request, 'import_file.html', {'form': form})
    else:
        form = ImportFileForm()

        return render(request, 'import_file.html', {'form': form})
