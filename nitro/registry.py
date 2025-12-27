# nitro_core/registry.py

# Global registry for components: "ClassName" -> Class
_components_registry = {}

def register_component(cls):
    """
    Decorator to register a Nitro component.
    Usage: @register_component class MyComponent...
    """
    _components_registry[cls.__name__] = cls
    return cls

def get_component_class(name: str):
    return _components_registry.get(name)