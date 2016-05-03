Install
=======

This section describes steps required for initial server preparation in order
to deploy ``CI Dashboard`` application.

All the configurations are done and tested on fresh installed ``Ubuntu 14.04 LTS (trusty)``.

1. Update & updade the system to retrive the fresh packages versions:
    ::

        $ sudo apt-get update
        $ sudo apt-get upgrade -y

2. Install ``MySQL`` database. During the installation process, you will be
    prompted to set a password for the MySQL root user. Keep it for future reference:
    ::

        $ sudo apt-get install -y mysql-server

3. Create a new user and database:
    ::

        $ mysql -u root -p # enter the root password that was set during the MySQL installation
        mysql> create database ci_dashboard_prod;
        mysql> create user 'dashboard'@'localhost' identified by 'pass123';  # remember the password
        mysql> grant all on ci_dashboard_prod.* to 'dashboard';
        mysql> exit

4. Install required project dependencies
    ::

        $ sudo apt-get install -y python-django python-jenkins python-django-south python-ldap python-django-auth-ldap python-mysqldb python-amqp python-celery python-jsonschema rabbitmq-server

5. Download and install the lattest ``CI Dashboard`` version.
    Project ``fuel-infra/packages/python-django-ci-status``:
    ::

        $ sudo dpkg -i python-django-ci-status_0.0.1+git14-ga4ecf08_all.deb  # example, version might differ

6. Set settings config for application and place it at ``/etc/ci_status/`` path:
    ::

        $ cat /etc/ci_status/settings.yaml

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

7. Run the application:
    ::

        $ cd /usr/lib/python2.7/dist-packages/
        $ export DJANGO_SETTINGS_MODULE=ci_dashboard.settings
        $ django-admin syncdb # setup superuser here
        $ django-admin migrate
        $ django-admin staff_group
        $ django-admin runserver 127.0.0.1:8080

8. Run the background scheduller:
    ::

        $ cd ~/ # or any folder with write access for simple user
        $ celery -A ci_dashboard worker -B -l info

You are done! :)

NOTE: For more secure production-ready installation you might want to consider
additional web-server above the Django application but it is a good starting point.
