from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

from ci_dashboard.constants import LDAP_USER_PERMISSIONS


class Command(BaseCommand):
    help = 'Set groups {} as staff'.format(", ".join(settings.STAFF_GROUPS))

    def handle(self, *args, **options):
        permissions = []
        for perm in LDAP_USER_PERMISSIONS:
            try:
                permissions.append(Permission.objects.get(codename=perm))
            except Permission.DoesNotExist:
                raise CommandError('Default application permission "%s" is missing' % perm)

        for ldap_group in settings.STAFF_GROUPS:
            group, _ = Group.objects.get_or_create(name=ldap_group)
            group.permissions.add(*permissions)
            group.save()

        self.stdout.write('LDAP groups was mapped successfully')
