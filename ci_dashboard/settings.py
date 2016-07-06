"""
Django settings for ci_dashboard project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os
import logging
import json

import site_settings

from django.contrib.messages import constants as messages

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, 'static', 'ci_dashboard')
]

DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'ci_dashboard',
]

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ci_dashboard.api.middleware.TokenAuthMiddleware',  # Authenticate using 'Token' header
]

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",

    "ci_dashboard.context_processors.last_sync",
)

ROOT_URLCONF = 'ci_dashboard.urls'

WSGI_APPLICATION = 'ci_dashboard.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)-8s %(name)-15s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'verbose console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django_auth_ldap': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'ci_dashboard': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

INTERNAL_IPS = ()

# Celery
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

STAFF_GROUPS = ('ci', 'devops-all')


def _load_schema(path):
    try:
        with open(path) as f:
            return json.loads(f.read())
    except IOError as exc:
        LOGGER.error(
            'Can not read `schema.json` file for import validation: %s', exc)
    except ValueError as exc:
        LOGGER.error('Can not parse `schema.json` file %s', exc)
    return None

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.json')
DEFAULT_SCHEMA_PATH = '/usr/share/ci-status/schema.json'

JSON_SCHEMA = _load_schema(
    SCHEMA_PATH if os.path.exists(SCHEMA_PATH) else DEFAULT_SCHEMA_PATH
)

site_settings.update_settings(globals(), 'CI_STATUS', '.:/etc/ci-status')
