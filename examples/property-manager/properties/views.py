from django.shortcuts import get_object_or_404, render

from .components.property_list import PropertyList  # Importar nuevo componente
from .components.tenant_manager import TenantManager
from .models import Property


def property_detail(request, property_id):
    # 1. Buscamos la propiedad (o 404 si no existe)
    prop = get_object_or_404(Property, id=property_id)

    # 2. Inicializamos el componente Nitro
    # Esto prepara el HTML inicial y el JSON oculto para SEO/Hidratación
    component = TenantManager(property_id=prop.id)

    return render(request, "property_detail.html", {
        "property": prop,
        "tenant_manager": component.render() # OJO: Llamamos a .render() aquí
    })

# def property_detail(request, property_id):
#     prop = get_object_or_404(Property, id=property_id)
#     # ¡Ya no instanciamos nada aquí! Solo mandamos la data básica.
#     return render(request, "property_detail.html", {"property": prop})

def property_list_view(request):
    # Inicializamos el componente vacío (cargará todas las propiedades)
    component = PropertyList()

    return render(request, "property_list.html", {
        "property_list_component": component.render()
    })
