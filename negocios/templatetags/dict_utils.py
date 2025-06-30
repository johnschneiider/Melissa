from django import template

register = template.Library()

@register.filter
def get(d, key):
    return d.get(key)

@register.filter
def lookup(d, key):
    try:
        return d[key]
    except (KeyError, TypeError):
        return ''
