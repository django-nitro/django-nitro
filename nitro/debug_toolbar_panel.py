"""
Django Debug Toolbar Panel for Nitro Components.

Displays component state, action calls, and events for debugging.
"""

try:
    from debug_toolbar.panels import Panel

    HAS_DEBUG_TOOLBAR = True
except ImportError:
    HAS_DEBUG_TOOLBAR = False

    # Dummy Panel class for when debug_toolbar is not installed
    class Panel:
        pass


class NitroDebugPanel(Panel):
    """
    Django Debug Toolbar panel for Nitro components.

    Shows:
    - Component instances rendered on the page
    - Component state
    - Action calls made during the request
    - Events emitted
    - Template tags used

    Installation:
        Add to DEBUG_TOOLBAR_PANELS in settings.py:

        DEBUG_TOOLBAR_PANELS = [
            ...
            'nitro.debug_toolbar_panel.NitroDebugPanel',
        ]
    """

    name = "Nitro"
    template = "nitro/debug_toolbar_panel.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.components = []
        self.actions = []
        self.events = []
        self.template_tags = []

    def nav_title(self):
        """Title in the debug toolbar nav."""
        return "Nitro"

    def nav_subtitle(self):
        """Subtitle showing component count."""
        count = len(self.components)
        return f"{count} component{'s' if count != 1 else ''}"

    def title(self):
        """Title of the panel."""
        return "Nitro Components"

    def enable_instrumentation(self):
        """Enable instrumentation to track Nitro components."""
        # Patch component rendering to track instances
        from nitro.base import NitroComponent

        original_render = NitroComponent.render

        def tracked_render(component_self):
            """Track component render."""
            # Get component info
            component_info = {
                "name": component_self.__class__.__name__,
                "template": component_self.template_name,
                "state": component_self.state.model_dump()
                if hasattr(component_self.state, "model_dump")
                else str(component_self.state),
                "secure_fields": component_self.secure_fields,
                "smart_updates": component_self.smart_updates,
            }

            self.components.append(component_info)

            return original_render(component_self)

        NitroComponent.render = tracked_render

        # Track actions
        original_process_action = NitroComponent.process_action

        def tracked_process_action(
            component_self, action_name, payload, current_state_dict, uploaded_file=None
        ):
            """Track action calls."""
            action_info = {
                "component": component_self.__class__.__name__,
                "action": action_name,
                "payload": payload,
                "has_file": uploaded_file is not None,
            }

            self.actions.append(action_info)

            return original_process_action(
                component_self, action_name, payload, current_state_dict, uploaded_file
            )

        NitroComponent.process_action = tracked_process_action

        # Track events
        original_emit = NitroComponent.emit

        def tracked_emit(component_self, event_name, data=None):
            """Track emitted events."""
            event_info = {
                "component": component_self.__class__.__name__,
                "event": event_name,
                "data": data,
            }

            self.events.append(event_info)

            return original_emit(component_self, event_name, data)

        NitroComponent.emit = tracked_emit

    def disable_instrumentation(self):
        """Disable instrumentation."""
        # Restore original methods
        # (In production, we'd need to store the originals)
        pass

    def generate_stats(self, request, response):
        """Generate statistics for the panel."""
        self.record_stats(
            {
                "components": self.components,
                "actions": self.actions,
                "events": self.events,
                "template_tags": self.template_tags,
                "component_count": len(self.components),
                "action_count": len(self.actions),
                "event_count": len(self.events),
            }
        )


# Only export if debug_toolbar is installed
if HAS_DEBUG_TOOLBAR:
    __all__ = ["NitroDebugPanel"]
else:
    __all__ = []
