Usage
=====

This page describes a few common usecases of the ``CI Dashboard`` system.
Assume the system is installed and configured. Check the appropriate sections
for it:

* `Install <install.html#install>`__
* `Configuration <configuration.html#configuration>`__

.. _import_new_configuraton:

Import New Configuration
^^^^^^^^^^^^^^^^^^^^^^^^
1. Login into system with your ``LDAP`` credentials by clicking on the ``Login`` button
   in a upper right corner.
2. Click on the ``Import CIs`` menu item placed in dropdown under logged in user name.
3. Choose file from the local machine of appropriate format and click on the ``Import`` button.

As a result user would be redirected to main page and new configuration would take place.
Short message about operation status or any errors during the import would be displayed there.

.. _check_the_ci_system_statuses_history:

Check The CI System statuses history
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. From the main page click on any ``CI System`` tab displayed at left side of the page.
2. The last 10 statuses for this system would be shown there.
3. Scroll down until the bottom and click on the ``here`` link.

As a result full ``CI System`` statuses history would be listed there, paginated by 10 records on page.

.. _automated_monitoring_with_dashboard:

Automated Monitoring With Dashboard
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Automated monitoring provides an easy and clean way to look on recent changes
of ``CI Systems``, displayed in table view with and option for automatic page reload.

1. From any page click on the ``Dashboard View`` link from the page toolbar.
2. Two tables for ``Product Statuses`` and ``CI Systems`` would be displayed there
   with the most recent statuses on the.
3. There is a possibility to enable/disabple automatic page reload every (5 minutes)
   by clicking on the ``Page Autorefresh`` button in the right corner at the bottom.

.. _manual_status_assignment:

Manual Status Assignment
^^^^^^^^^^^^^^^^^^^^^^^^

In cases when the user has some additional information about ``CI System`` status
or availability it might be usefull to have a possibility to assign the status
manually. In order to do it:

1. Click on the ``New Status`` button at right upper corner of page toolbar or
   click on the ``Set New Status`` button placed at each ``CI System`` card
   on main page.
2. At new page openned, choose on of the predefined status types.
3. Provide a short summary about this new status.
4. There is a possibility to add an optional full-length description that will
   be availabe at status detail page.
5. There also a possibility to mark a status as ``Manuall`` by selecting appropriate
   checkbox. At the moment this option is used to disable automated reassignment
   of the status from ``Fail`` to ``Success`` in order to stimulate each status
   failure review by a person.
6. Click on the ``Submit`` button to save the status.

As a result new status will be created, user would be redirected to status detail
page for future review.

.. _status_update:

Status Update
^^^^^^^^^^^^^

There is a possibility to manually update any assigned status, either automated
or manual.
It might be usefull in cases when additonal description added or when user has
some information that allows status correction after automated assignment.

1. Click on the ``Details`` button or link (depends on the context) that places on
   every status card/item.
2. At status detail page openned, click the ``Edit`` button.
3. Make required changes and save them as by clicking on the ``Submit`` button.

As a result selected status will be updated, user would be redirected to status detail
page for future review.

.. _status_delete:

Status Delete
^^^^^^^^^^^^^

By design of the ``CI Dashboard`` doesn't delete any information it collected during
monitoring. The only way to do it is remove by hands.

1. Click on the ``Details`` button or link (depends on the context) that places on
   every status card/item.
2. At status detail page openned, click the ``Delete`` button.
3. Confirm status deletion by clicking on the ``Delete`` button again.

As a result selected status will be deleted, user would be redirected to the main page.

.. _advanced_manual_management:

Advanced Manual Management
^^^^^^^^^^^^^^^^^^^^^^^^^^

The post powerfull possibilities of manual configuration and tuning are accessable
by the superadmin interface that available only for user with appropriate permissions.

1. As logged in superadmin user click on the ``Admin Panel`` menu item placed
   in dropdown under logged in user name.
2. User will be redirected to administration panel were CRUD operations over all
   known objects will be available.

Use with care!
