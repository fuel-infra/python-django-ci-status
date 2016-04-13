from django import template
from django.conf import settings

from ci_system import constants

from ci_system.models import Status


register = template.Library()


@register.filter(name='status_color')
def status_color(status):
    status_type = status.status_type if type(status) is Status else status

    if status_type == constants.STATUS_SUCCESS:
        result = 'success'
    elif status_type == constants.STATUS_IN_PROGRESS:
        result = 'default'
    elif status_type == constants.STATUS_FAIL:
        result = 'danger'
    elif status_type == constants.STATUS_ERROR:
        result = 'warning'
    else:
        result = 'info'

    return result


@register.filter(name='can_manage_statuses')
def can_manage_statuses(user):
    if getattr(user, 'ldap_user', None):  # ldap users should have ldap groups
        return bool(set(settings.STAFF_GROUPS) & user.ldap_user.group_names)

    # all others should belong to django group (if added manually)
    # or be the superuser
    return bool(
        set(settings.STAFF_GROUPS) & {g.name for g in user.groups.all()}
    ) or user.is_superuser


@register.filter('fieldtype')
def fieldtype(field):
    return field.field.widget.__class__.__name__


@register.filter(name='status_text_for_type')
def status_text_for_type(status_type):
    return Status.text_for_type(status_type)


@register.filter(name='active_status_time')
def active_status_time(product_ci, version):
    return product_ci.active_status_time(version)


@register.filter(name='add_class')
def add_class(field, css):
    class_old = field.field.widget.attrs.get('class', None)
    class_new = (class_old + ' ' + css) if class_old else css
    return field.as_widget(attrs={"class": class_new})


@register.filter(name='sorted_by_rule_name')
def sorted_by_rule_name(rule_checks):
    return sorted(rule_checks, key=lambda rc: rc.rule.name)
