Install
=======

This section describes steps required for initial server preparation in order
to deploy ``CI Dashboard`` application.

All the configurations are done and tested on fresh installed ``Ubuntu 16.04 LTS (xenial)``.

1. Update & upgrade the system to retrieve the fresh packages versions:
    ::

        $ sudo apt-get update
        $ sudo apt-get upgrade -y

2. Install ``MySQL`` database and python bindings. During the installation process, you will be
    prompted to set a password for the MySQL root user. Keep it for future reference:
    ::

        $ sudo apt-get install -y mysql-server python-pymysql


3. Create a new user and database:
    ::

        $ mysql -u root -p  # enter the root password that was set during the MySQL installation
        mysql> create database ci_dashboard_prod;
        mysql> create user 'dashboard'@'localhost' identified by 'pass123';
        mysql> grant all on ci_dashboard_prod.* to 'dashboard'@'localhost';
        mysql> exit

4. Install the lattest ``CI Dashboard`` version.
    ::

        $ apt-get install -y python-django-ci-status

5. Set settings config for application and place it at ``/etc/ci-status/`` path:
    ::

        $ cat /etc/ci-status/settings.yaml

        DEBUG: False
        TEMPLATE_DEBUG: False

        SECRET_KEY: 'some long random string here'

        DATABASES:
          default:
            ENGINE: 'django.db.backends.mysql'
            NAME: ci_dashboard_prod
            USER: dashboard
            PASSWORD: pass123
            HOST: localhost
            PORT: ''

        AUTH_LDAP_SERVER_URI: 'ldap://custom_server.net'
        LDAP_GROUP_SETTINGS: 'cn=mirantis,ou=groups,o=mirantis,dc=mirantis,dc=net'
        AUTH_LDAP_GROUP_SEARCH:
          base_dn: 'ou=groups,o=mirantis,dc=mirantis,dc=net'
          scope: 'SCOPE_SUBTREE'
          filterstr: '(objectClass=groupOfNames)'
        AUTH_LDAP_USER_DN_TEMPLATE: 'uid=%(user)s,ou=people,o=mirantis,dc=mirantis,dc=net'
        AUTH_LDAP_USERS_BASE_DN: 'ou=people,o=mirantis,dc=mirantis,dc=net'
        AUTH_LDAP_GROUP_CACHE_TIMEOUT: 3600

        STAFF_GROUPS:
          - 'ci'
          - 'devops-all'

        INTERNAL_IPS:
          - '127.0.0.1'  # if runned on localhost

        CELERYBEAT_SCHEDULE:
          every_ten_minutes:
            task: 'ci_dashboard.tasks.synchronize'
            schedule:
              crontab:
                minute: '*/10'

6. Run the application:

    6.1 Standalone run

        ::

            $ ci-status migrate
            $ ci-status staff_group
            $ ci-status import_config config.yaml  # only if you have configuration
            $ ci-status update
            $ ci-status runserver 127.0.0.1:8080

    6.2 UWSGI + nginx run

        ::

            $ sudo apt-get install python-django-ci-status-uwsgi-nginx
            $ ci-status migrate
            $ ci-status staff_group
            $ ci-status import_config config.yaml  # only if you have configuration
            $ ci-status update
            $ sudo service uwsgi start
            $ sudo service nginx start

    6.3 UWSGI configuration for application

        ::

            uwsgi:
              plugins: python
              env: DJANGO_SETTINGS_MODULE=ci_dashboard.settings
              module: ci_dashboard.wsgi:application
              master: True
              processes: 5
              socket: 127.0.0.1:6776
              vacuum: True
              die-on-term: true
              uid: ci-status
              gid: ci-status

7. Install ``RabbitMQ`` server as a transport for celery tasks and celery itself:
    ::

         $ sudo apt-get install -y rabbitmq-server celery-common

8. Run the background scheduller:
    ::

        $ celery -A ci_dashboard worker -B -l info

You are done! :)

NOTE: For more secure production-ready installation you might want to consider
additional web-server above the Django application but it is a good starting point.
