import os

from django import template
from django.templatetags.static import static

register = template.Library()


@register.simple_tag(takes_context=True)
def static_asset(context, asset_path):
    if context.get('debug', False):
        return static(asset_path)

    path, extension = os.path.splitext(asset_path)
    return static('{}.min{}'.format(path, extension))
