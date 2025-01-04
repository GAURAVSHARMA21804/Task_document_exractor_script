import base64
from django import template

register = template.Library()

@register.filter(name='b64encode')
def b64encode(value):
    """Encodes binary image data to base64 for inline image rendering."""
    if value:
        return base64.b64encode(value).decode('utf-8')
    return ''
