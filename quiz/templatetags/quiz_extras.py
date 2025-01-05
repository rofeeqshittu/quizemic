from django import template

register = template.Library()

@register.filter
def modulo(value, arg):
    """Returns the remainder of value divided by arg"""
    return value % arg

@register.filter
def integer_divide(value, arg):
    """Returns integer division of value by arg"""
    return value // arg

@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary using the key"""
    return dictionary.get(str(key))
