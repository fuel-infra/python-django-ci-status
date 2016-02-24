from ci_dashboard.models import Stats


def last_sync(request):
    last_sync, created = Stats.objects.get_or_create(name='last_sync')

    return {
        'last_sync': last_sync.updated_at.isoformat(),
    }
