# nitro/templatetags/nitro_tags.py
from django import template

from nitro.registry import get_component_class

register = template.Library()


@register.simple_tag(takes_context=True)
def nitro_component(context, component_name, **kwargs):
    ComponentClass = get_component_class(component_name)
    if not ComponentClass:
        return ""

    # Extraemos el request del contexto
    request = context.get("request")

    # Lo inyectamos al instanciar
    instance = ComponentClass(request=request, **kwargs)
    return instance.render()
