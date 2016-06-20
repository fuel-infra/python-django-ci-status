Configuration
=============

There are two ways to configure ``CI Dashboard``:
  * manually
  * by import

.. _manual_configuration:

Manual Configuration
^^^^^^^^^^^^^^^^^^^^

Manual configuration requries logged in user with an ``superadmin`` permissions.
After that all the configuration details could be changed/updated from web-ui
which is accessable on the ``/admin`` endpoint. The link to it is located
under the user profile selector.

.. _import_configuration:

Import Configuration
^^^^^^^^^^^^^^^^^^^^

More common, repeatable and easy to automate way of configuration of the
``CI Dashboard`` is by importing .yaml/.yml files of specific format.
To achive this goal user should be logged in and belongs to either ``ci`` or
``devops-all`` LDAP groups.
Then on the ``/import_file/`` endpoint which is accesable from the web-ui by
link under user profile selector, user could select the file from its local
machine and click the ``Import`` button to proccess.
After redirect on main page user gets response about import result (was it
successfull or not, errors if any) and new configuration would be applied for
the system.

.. _import_file_format:

Import File Format
^^^^^^^^^^^^^^^^^^

Full-featured import file looks like this::

  dashboards:
    products:
      - version: master
        sections:
          - title: Master Product
            key: mcb
      - version: '9.0'
        sections:
          - title: Product 9.0
            key: 90cb
          - title: Tempo 9.0
            key: 90tp

    ci_systems:
      - title: Public packaging CI
        key: ppci
      - title: Fuel CI
        key: fci

  sources:
    jenkins:
      - url: https://product-ci.infra.test/
        query:
          jobs:
            - names:
                - '9.0.all'
                - '9.0.test_all'
              filter:
                triggered_by: Any
              dashboards:
                - ppci
                - 90cb
                - mcb
            - names:
                - '9.0.swarm.timer.stable'
              filter:
                triggered_by: Any
              dashboards:
                - ppci
                - mcb
          views:
            - names:
                - '10.0'
              filter:
                triggered_by: Any
                gerrit_refspec: 'refs/head/master'
              dashboards:
                - ppci
                - mcb
      - url: https://ci.fuel.test/
        query:
          jobs:
            - names:
                - fuellib_noop_tests
                - master.fuel-library.pkgs.ubuntu.neutron_vlan_ha
              filter:
                triggered_by: Any
              dashboards:
                - fci
                - 90cb
            - names:
                - master.fuel-web.pkgs.ubuntu.review_fuel_web_deploy
              filter:
                triggered_by: Any
                gerrit_branch: trunk
                gerrit_refspec: 'refs/head/trunk'
              dashboards:
                - fci
                - mcb
          views:
            - names:
                - docs
              filter:
                triggered_by: Any
                gerrit_branch: master
              dashboards:
                - fci
                - mcb
                - 90tp


:dashboards: the list of systems and products to be displayed in ``CI Dashboard``
:products: the list of ``Product Statuses`` scoped by version name
:version: string value of ``Product Status`` version
:sections: each seaction describes one or many ``Product Statuses`` which are sharing same version
:title: the title of ``Product Status``
:key: uniq string key used as reference for checks assignment in the config file
:ci_systems: the list of ``CI Systems`` to be displayed in ``CI Dashboard``
:title: the name of the ``CI System``
:key: uniq string key used as reference for checks assignment in the config file
:sources: the list of backend definitons of ``CI Systems`` and its jobs, mapped to real ``Jenkins`` instances
:url: the url of the ``Jenkins`` system
:query: the list of ``Jenkins`` jobs and views to be checked on this server
:jobs: the list of ``Jenkins`` jobs configurations on selected server
:views: the list of ``Jenkins`` views configurations on selected server. Each view rule is checked
  against all the jobs belongs to it
:names: the list of ``Jenkins`` jobs/views that shares common filters or dashboards
:filter: ``GERRTIT_`` filters on specific job/view. Currently supported filters are:

  * :gerrit_refspec: string representation of refspec where the event occurs. For example 'refs/head/master'
  * :gerrit_branch: string representation of branch where the event occurs. For example 'master'
  * :triggered_by: ``Jenkins`` job trigger issuer type. One from the list ['Timer', 'Gerrit trigger', 'Manual', 'Any']. Default is 'Timer'
:dashboards: the list of ``CI Systems`` and ``Product Statuses`` keys on which jobs and views defined above would afffect the status change. Only one ``CI System`` could be presented here as it maps to the url in a uniq way

.. _import_by_web_request:

Configure using command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a custom command to ``ci-status`` to update config from configurations file:

  $ ci-status import_config config.yaml

Import By Web Request
^^^^^^^^^^^^^^^^^^^^^

Additionally there is a possibility to import system configuration via HTTP POST request
on the ``api/import_file`` endpoint. It could be done by the ``curl`` tool for example.
File data stream and authentiction credentials should be present in this request.
For example::

  $ curl -X POST -F file=@/home/user/config.yaml -F username=tasty -F password='toast!123' ci-status.dev.mirantis.net/api/import_file/

The response on this request would contain short description and status of the
operation in json format.
