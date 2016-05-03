from __future__ import absolute_import

import os
import yaml

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured


def load_yaml(filename, conf_dirs):
    for conf_dir in conf_dirs:
        path = os.path.join(conf_dir, filename)

        if os.path.exists(path):
            with open(path) as f:
                return yaml.safe_load(f)

    raise ImproperlyConfigured('%s not found in %r' % (filename, conf_dirs))


def process_ldap_settings_dict(settings):
    if 'AUTH_LDAP_SERVER_URI' not in settings:
        return

    import ldap
    from django_auth_ldap.config import GroupOfNamesType, LDAPSearch

    # settings['AUTH_LDAP_BIND_AS_AUTHENTICATING_USER'] = True
    settings['AUTH_LDAP_GROUP_TYPE'] = GroupOfNamesType()
    settings['AUTHENTICATION_BACKENDS'] = (
        'django.contrib.auth.backends.ModelBackend',
        'django_auth_ldap.backend.LDAPBackend',
    )

    LDAP_GROUP_SETTINGS = settings['LDAP_GROUP_SETTINGS']

    settings['AUTH_LDAP_USER_FLAGS_BY_GROUP'] = {
        'is_staff': LDAP_GROUP_SETTINGS,
    }

    settings['AUTH_LDAP_REQUIRE_GROUP'] = LDAP_GROUP_SETTINGS
    settings['AUTH_LDAP_USER_ATTR_MAP'] = {
        'first_name': 'givenName',
        'last_name': 'sn',
        'email': 'mail'
    }

    settings['AUTH_LDAP_CONNECTION_OPTIONS'] = {
        ldap.OPT_DEBUG_LEVEL: int(settings.get('DEBUG', False)),
        ldap.OPT_REFERRALS: 0,
    }

    settings['AUTH_LDAP_MIRROR_GROUPS'] = True
    settings['AUTH_LDAP_FIND_GROUP_PERMS'] = True
    settings['AUTH_LDAP_CACHE_GROUPS'] = True

    group_search = settings.get('AUTH_LDAP_GROUP_SEARCH')

    if group_search:
        if 'scope' in group_search:
            group_search['scope'] = getattr(ldap, group_search['scope'])

        settings['AUTH_LDAP_GROUP_SEARCH'] = LDAPSearch(**group_search)

    if settings.get('DEBUG', False):
        import logging
        logger = logging.getLogger('django_auth_ldap')
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG)


def process_celery_settings_dict(settings):
    if 'CELERYBEAT_SCHEDULE' not in settings:
        return

    celery_settings = settings['CELERYBEAT_SCHEDULE']
    for record in celery_settings.values():
        if 'crontab' in record.get('schedule', {}):
            record['schedule'] = crontab(**record['schedule']['crontab'])

    settings['CELERYBEAT_SCHEDULE'] = celery_settings


def update_settings(settings,
                    conf_path_envvar,
                    conf_path_default,
                    filename='settings.yaml'):
    conf_path = os.getenv(conf_path_envvar, conf_path_default)
    conf_dirs = settings['SITE_CONF_DIRS'] = conf_path.split(':')

    _site_settings_dict = load_yaml(filename, conf_dirs)
    process_ldap_settings_dict(_site_settings_dict)
    process_celery_settings_dict(_site_settings_dict)

    settings.update(_site_settings_dict)
