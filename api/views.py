import json

from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ci_system.models import CiSystem


@csrf_exempt
def import_file(request):
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
