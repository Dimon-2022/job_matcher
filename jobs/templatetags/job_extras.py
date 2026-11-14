from django import template
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def ago(value):
    return timesince(value, depth=1)