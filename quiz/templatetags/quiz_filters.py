# quiz/templatetags/quiz_filters.py
from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    css_classes = value.field.widget.attrs.get('class', '')
    if css_classes:
        css_classes = f"{css_classes} {arg}"
    else:
        css_classes = arg
    return value.as_widget(attrs={'class': css_classes})

@register.filter
def divide(value, arg):
    """Divides the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divisibleby(value, arg):
    """Return the integer division of value by arg"""
    return value // arg

@register.filter
def modulo(value, arg):
    """Return the remainder of value divided by arg"""
    return value % arg

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key"""
    return dictionary.get(str(key))
