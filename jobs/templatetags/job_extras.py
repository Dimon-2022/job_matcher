from datetime import timedelta

from django import template
from django.utils import timezone
from django.utils.timesince import timesince
from jobs.geo import flag as country_flag

register = template.Library()


@register.filter
def ago(value):
    if timezone.now() - value < timedelta(minutes=1):
        return "just now"
    return f"{timesince(value, depth=1)} ago"

@register.filter
def flag(code):
    return country_flag(code or "")