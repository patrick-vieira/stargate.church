import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

_REALCE = re.compile(r"\*([^*]+)\*")


@register.filter
def realce(titulo):
    """Escapa o título e só depois troca `*palavra*` por <em class="sg-realce">."""
    escapado = conditional_escape(titulo)
    return mark_safe(_REALCE.sub(r'<em class="sg-realce">\1</em>', escapado))


@register.filter
def sem_realce(titulo):
    """O título sem os asteriscos de realce (para <title>, cards, etc.)."""
    return _REALCE.sub(r"\1", str(titulo))
