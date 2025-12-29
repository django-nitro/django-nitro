import json
import logging
from typing import Any, Generic, TypeVar, get_args

from django.conf import settings
from django.core.signing import BadSignature, Signer
from django.db import models
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

S = TypeVar("S", bound=BaseModel)


class NitroComponent(Generic[S]):
    """
    Abstract base class for Nitro components.

    Nitro components provide reactive UI updates through AlpineJS integration,
    with server-side state management and integrity verification.

    Type parameter S should be a Pydantic BaseModel representing the component's state schema.

    Attributes:
        template_name: Path to the Django template for rendering this component
        state_class: Pydantic model class for state validation and type safety
        secure_fields: List of field names that require integrity verification
        toast_enabled: Enable/disable toasts for this component (None = use global setting)
        toast_position: Toast position (None = use global setting)
        toast_duration: Toast duration in ms (None = use global setting)
        toast_style: Toast style (None = use global setting)
        smart_updates: Enable smart state diffing for large lists (default: False)
    """

    template_name: str = ""
    component_id: str = ""
    state_class: type[S] | None = None
    state: S
    secure_fields: list[str] = []

    # Toast configuration (None = use global settings)
    toast_enabled: bool | None = None
    toast_position: str | None = None
    toast_duration: int | None = None
    toast_style: str | None = None

    # Smart updates configuration
    smart_updates: bool = False

    def __init__(self, request: HttpRequest | None = None, initial_state: dict = None, **kwargs):
        """
        Initialize a Nitro component.

        Args:
            request: The HTTP request object (optional)
            initial_state: Dictionary to hydrate the component state (for server-side processing)
            **kwargs: Additional arguments passed to get_initial_state()
        """
        self.request = request
        self.component_id = f"{self.__class__.__name__.lower()}-{id(self)}"
        self._signer = Signer()
        self._pending_errors: dict[str, str] = {}
        self._pending_messages: list[dict[str, str]] = []
        self._pending_events: list[dict[str, Any]] = []

        if initial_state is not None:
            if self.state_class:
                self.state = self.state_class(**initial_state)
            else:
                self.state = initial_state  # type: ignore
        else:
            self.state = self.get_initial_state(**kwargs)

    def get_initial_state(self, **kwargs) -> S:
        """
        Generate the initial state for this component.

        This method must be implemented by subclasses to define how
        the component's state is initialized.

        Args:
            **kwargs: Context-specific arguments for state initialization

        Returns:
            An instance of the component's state schema

        Raises:
            NotImplementedError: This method must be overridden
        """
        raise NotImplementedError

    @property
    def current_user(self):
        """
        Shortcut to request.user with authentication check.

        Returns:
            The authenticated user object, or None if user is not authenticated.

        Example:
            def create_item(self):
                if self.current_user:
                    item.owner = self.current_user
                    item.save()
        """
        if self.request and self.request.user.is_authenticated:
            return self.request.user
        return None

    @property
    def is_authenticated(self):
        """
        Check if current user is authenticated.

        Returns:
            True if user is authenticated, False otherwise

        Example:
            def get_base_queryset(self, search='', filters=None):
                if not self.is_authenticated:
                    return queryset.none()
                return queryset.filter(owner=self.current_user)
        """
        return self.request and self.request.user.is_authenticated

    def require_auth(self, message: str = "Authentication required") -> bool:
        """
        Enforce authentication requirement.

        Shows error message and returns False if user is not authenticated.

        Args:
            message: Custom error message. Default: "Authentication required"

        Returns:
            True if user is authenticated, False otherwise

        Example:
            def delete_item(self, id: int):
                if not self.require_auth("You must be logged in to delete"):
                    return  # User not authenticated, error shown

                # Proceed with deletion
                super().delete_item(id)
        """
        if not self.is_authenticated:
            self.error(message)
            return False
        return True

    def _get_toast_config(self) -> dict[str, Any]:
        """
        Get toast configuration for this component.

        Component-level settings override global settings from Django settings.

        Returns:
            Dictionary with toast configuration:
            - enabled: bool
            - position: str
            - duration: int
            - style: str
        """
        from nitro.conf import get_setting

        return {
            "enabled": (
                self.toast_enabled
                if self.toast_enabled is not None
                else get_setting("TOAST_ENABLED")
            ),
            "position": self.toast_position or get_setting("TOAST_POSITION"),
            "duration": (
                self.toast_duration
                if self.toast_duration is not None
                else get_setting("TOAST_DURATION")
            ),
            "style": self.toast_style or get_setting("TOAST_STYLE"),
        }

    def _compute_integrity(self) -> str:
        """
        Compute an integrity token for secure fields.

        Creates an HMAC-based signature of the values in secure_fields
        to prevent client-side tampering.

        Returns:
            A signed token string, or empty string if no secure fields are defined
        """
        if not self.secure_fields:
            return ""
        state_dump = self.state.model_dump() if hasattr(self.state, "model_dump") else self.state
        data_to_sign = "|".join([f"{k}:{state_dump.get(k)}" for k in self.secure_fields])
        return self._signer.sign(data_to_sign)

    def verify_integrity(self, token: str | None) -> bool:
        """
        Verify that secure fields haven't been tampered with.

        Compares the provided integrity token against the current state
        to ensure data integrity.

        Args:
            token: The integrity token from the client

        Returns:
            True if verification passes or no secure fields exist, False otherwise
        """
        if not self.secure_fields:
            return True
        if not token:
            return False
        try:
            original_data = self._signer.unsign(token)
            state_dump = (
                self.state.model_dump() if hasattr(self.state, "model_dump") else self.state
            )
            current_data = "|".join([f"{k}:{state_dump.get(k)}" for k in self.secure_fields])
            return original_data == current_data
        except BadSignature:
            return False

    def _compute_diff(self, old_state: dict, new_state: dict) -> dict:
        """
        Compute diff between old and new state.

        Only includes changed fields in the diff. For lists with items
        that have 'id' fields, computes added/removed/updated operations.

        Args:
            old_state: Previous state dictionary
            new_state: Current state dictionary

        Returns:
            Dictionary with only changed fields. List fields with 'id'
            items are returned as {"diff": {"added": [], "removed": [], "updated": []}}
        """
        diff = {}

        for key, new_value in new_state.items():
            old_value = old_state.get(key)

            # Skip if values are equal
            if old_value == new_value:
                continue

            # Check if it's a list with items that have 'id'
            if isinstance(new_value, list) and isinstance(old_value, list):
                if new_value and isinstance(new_value[0], dict) and "id" in new_value[0]:
                    # Compute list diff
                    list_diff = self._diff_list(old_value, new_value)
                    if list_diff["added"] or list_diff["removed"] or list_diff["updated"]:
                        diff[key] = {"diff": list_diff}
                    continue

            # Regular field change
            diff[key] = new_value

        return diff

    def _diff_list(self, old_list: list, new_list: list) -> dict:
        """
        Compute diff for lists with items that have 'id' field.

        Args:
            old_list: Previous list of items
            new_list: Current list of items

        Returns:
            Dictionary with:
            - added: List of new items
            - removed: List of removed item IDs
            - updated: List of updated items (full item dict)
        """
        # Build ID mappings
        old_ids = {
            item.get("id"): item
            for item in old_list
            if isinstance(item, dict) and "id" in item
        }
        new_ids = {
            item.get("id"): item
            for item in new_list
            if isinstance(item, dict) and "id" in item
        }

        # Detect changes
        added = [item for id, item in new_ids.items() if id not in old_ids]
        removed = [id for id in old_ids if id not in new_ids]
        updated = [item for id, item in new_ids.items() if id in old_ids and item != old_ids[id]]

        return {"added": added, "removed": removed, "updated": updated}

    def add_error(self, field: str, message: str):
        """Add a field-specific validation error to be sent to the client."""
        self._pending_errors[field] = message

    def success(self, message: str):
        """Add a success message to be displayed to the user."""
        self._pending_messages.append({"level": "success", "text": message})

    def error(self, message: str):
        """Add an error message to be displayed to the user."""
        self._pending_messages.append({"level": "error", "text": message})

    def warning(self, message: str):
        """Add a warning message to be displayed to the user."""
        self._pending_messages.append({"level": "warning", "text": message})

    def info(self, message: str):
        """Add an info message to be displayed to the user."""
        self._pending_messages.append({"level": "info", "text": message})

    def _sync_field(self, field: str, value: Any):
        """
        Internal method for auto-syncing fields (used by {% nitro_model %} tag).

        This method is called automatically by the nitro_model template tag
        to sync individual fields without requiring explicit action methods.

        Args:
            field: Field name to sync (e.g., 'email', 'search', 'user.profile.name')
            value: New value for the field

        Example:
            # In template (Zero JS Mode)
            <input {% nitro_model 'email' %}>
            <input {% nitro_model 'user.profile.email' %}>

            # This automatically calls:
            call('_sync_field', {field: 'email', value: 'user@example.com'})
            call('_sync_field', {field: 'user.profile.email', value: 'user@example.com'})

        Note:
            - This is a silent operation (no success messages)
            - Validation errors are added to _pending_errors
            - Supports nested fields with dot notation (e.g., 'user.email')
        """
        # Handle nested fields (dot notation)
        if '.' in field:
            # Split field path (e.g., 'user.profile.email' -> ['user', 'profile', 'email'])
            parts = field.split('.')

            # Navigate to the parent object
            obj = self.state
            for part in parts[:-1]:
                if not hasattr(obj, part):
                    if settings.DEBUG:
                        raise ValueError(
                            f"Nested field path '{field}' is invalid: "
                            f"'{part}' does not exist in {obj.__class__.__name__}"
                        )
                    # In production, silently ignore
                    return
                obj = getattr(obj, part)

            # Set the final field value
            final_field = parts[-1]
            if not hasattr(obj, final_field):
                if settings.DEBUG:
                    available_fields = ", ".join(
                        f for f in dir(obj) if not f.startswith("_")
                    )
                    raise ValueError(
                        f"Field '{final_field}' does not exist in {obj.__class__.__name__}. "
                        f"Available fields: {available_fields}"
                    )
                # In production, silently ignore
                return

            try:
                setattr(obj, final_field, value)
            except ValidationError as e:
                # Pydantic validation failed
                error_msg = str(e.errors()[0]["msg"]) if e.errors() else str(e)
                self._pending_errors[field] = error_msg
        else:
            # Simple field (no nesting)
            # Validate field exists in state
            if not hasattr(self.state, field):
                if settings.DEBUG:
                    # In debug mode, show helpful error
                    available_fields = ", ".join(
                        f for f in dir(self.state) if not f.startswith("_")
                    )
                    raise ValueError(
                        f"Field '{field}' does not exist in {self.state.__class__.__name__}. "
                        f"Available fields: {available_fields}"
                    )
                # In production, silently ignore
                return

            # Set the field value
            try:
                setattr(self.state, field, value)
            except ValidationError as e:
                # Pydantic validation failed
                error_msg = str(e.errors()[0]["msg"]) if e.errors() else str(e)
                self._pending_errors[field] = error_msg

    def _handle_file_upload(self, field: str, uploaded_file=None):
        """
        Internal method for handling file uploads (used by {% nitro_file %} tag).

        This method is called automatically by the nitro_file template tag
        when a file is uploaded. Override this method in your component to
        handle the file storage and processing.

        Args:
            field: Field name (e.g., 'avatar', 'document')
            uploaded_file: Django UploadedFile object

        Example:
            # Override in your component
            def _handle_file_upload(self, field: str, uploaded_file=None):
                if field == 'avatar':
                    # Save to media folder
                    from django.core.files.storage import default_storage
                    filename = default_storage.save(
                        f'avatars/{uploaded_file.name}',
                        uploaded_file
                    )
                    self.state.avatar_url = default_storage.url(filename)
                    self.success('Avatar uploaded successfully!')

                elif field == 'document':
                    # Process document
                    content = uploaded_file.read()
                    # ... process content ...
                    self.success('Document uploaded and processed!')

        Note:
            - This is a base implementation that does nothing
            - You must override this in your component to handle files
            - The uploaded file is available via self.request.FILES
        """
        # Base implementation - override in subclass
        if uploaded_file:
            self.warning(
                f"File '{uploaded_file.name}' was uploaded but not processed. "
                f"Override _handle_file_upload() in your component to handle it."
            )
        else:
            self.error("No file was uploaded")

    def emit(self, event_name: str, data: dict[str, Any] | None = None):
        """
        Emit a custom event to be sent to the client.

        Events are dispatched as DOM events that can be caught by other
        components or JavaScript code.

        Args:
            event_name: Name of the event (will be prefixed with 'nitro:' if not already)
            data: Optional data payload for the event

        Example:
            # In one component
            self.emit('user-updated', {'user_id': 123, 'name': 'John'})

            # In another component's template
            <div @nitro:user-updated.window="call('refresh')">...</div>
        """
        if not event_name.startswith("nitro:"):
            event_name = f"nitro:{event_name}"

        self._pending_events.append({"name": event_name, "data": data or {}})

    def refresh_component(self, component_id: str):
        """
        Helper method to trigger a refresh on another component.

        Emits a 'nitro:refresh-{component_id}' event that the target
        component should listen for.

        Args:
            component_id: ID of the component to refresh (lowercase)

        Example:
            # In component A
            self.refresh_component('propertylist')

            # In PropertyList template
            <div @nitro:refresh-propertylist.window="call('refresh')">...</div>
        """
        self.emit(f"refresh-{component_id.lower()}", {"source": self.__class__.__name__})

    def render(self):
        """
        Render the component as HTML with embedded AlpineJS state.

        Creates a wrapper div with x-data directive containing the component's
        state, errors, messages, and integrity token. The template is rendered
        inside this wrapper.

        Returns:
            SafeString containing the complete HTML for the component
        """
        state_dict = self.state.model_dump() if hasattr(self.state, "model_dump") else self.state

        # Package everything for the JavaScript layer
        full_payload = {
            "state": state_dict,
            "errors": {},
            "messages": [],
            "integrity": self._compute_integrity(),
            "toast_config": self._get_toast_config(),
        }

        context = {"state": state_dict, "component": self}
        if self.request:
            context["request"] = self.request

        html_content = render_to_string(self.template_name, context)

        # Store JSON in a data attribute (Django auto-escapes)
        # Use single quotes for the attribute value to avoid escaping issues
        wrapper = f"""
        <div id="{self.component_id}"
             data-nitro-state='{json.dumps(full_payload)}'
             x-data="nitro('{self.__class__.__name__}', $el)"
             class="nitro-component">
            {html_content}
        </div>
        """
        return mark_safe(wrapper)

    def process_action(
        self, action_name: str, payload: dict, current_state_dict: dict, uploaded_file=None
    ):
        """
        Process an action call from the client.

        This is called by the API dispatch endpoint when a client triggers an action.
        It hydrates the state, calls the action method, and returns the updated state.

        Args:
            action_name: Name of the action method to call
            payload: Arguments to pass to the action method
            current_state_dict: Current state from the client
            uploaded_file: Optional uploaded file from the client

        Returns:
            Dictionary containing updated state, errors, messages, integrity token,
            toast config, and events. If smart_updates is enabled, state may be a diff
            and partial will be True.

        Raises:
            ValueError: If the action method doesn't exist on this component
        """
        # Store old state for diffing if smart_updates enabled
        old_state_dict = current_state_dict.copy() if self.smart_updates else None

        try:
            if self.state_class:
                self.state = self.state_class(**current_state_dict)
            else:
                dummy = self.get_initial_state(**current_state_dict)
                self.state = type(dummy)(**current_state_dict)
        except Exception as e:
            logger.error(
                "Failed to hydrate state for component %s with data: %s. Error: %s",
                self.__class__.__name__,
                current_state_dict,
                str(e),
                exc_info=True,
            )
            raise

        if hasattr(self, action_name):
            action_method = getattr(self, action_name)

            # Check if action accepts uploaded_file parameter
            import inspect

            sig = inspect.signature(action_method)
            if "uploaded_file" in sig.parameters:
                action_method(**payload, uploaded_file=uploaded_file)
            else:
                action_method(**payload)

            # Get new state
            new_state_dict = (
                self.state.model_dump() if hasattr(self.state, "model_dump") else self.state
            )

            # Compute diff if smart_updates enabled
            if self.smart_updates and old_state_dict:
                state_to_send = self._compute_diff(old_state_dict, new_state_dict)
            else:
                state_to_send = new_state_dict

            return {
                "state": state_to_send,
                "partial": self.smart_updates,  # Signal to client that this is a diff
                "errors": self._pending_errors,
                "messages": self._pending_messages,
                "integrity": self._compute_integrity(),
                "toast_config": self._get_toast_config(),
                "events": self._pending_events,
            }
        raise ValueError(f"Action {action_name} not found")


class ModelNitroComponent(NitroComponent[S]):
    """
    Nitro component with Django ORM integration.

    Extends NitroComponent with automatic model loading, queryset support,
    and automatic secure field detection for database IDs and foreign keys.

    IMPORTANT: Your state schema MUST use ConfigDict(from_attributes=True)
    when working with Django models. This allows Pydantic to read Django
    model attributes correctly.

    Example:
        from pydantic import BaseModel, ConfigDict

        class PropertyState(BaseModel):
            model_config = ConfigDict(from_attributes=True)

            id: int
            name: str
            address: str

    Attributes:
        model: Django model class associated with this component
    """

    model: type[models.Model] | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model:
            if "id" in self.state_class.model_fields:
                self.secure_fields.append("id")
            for field in self.state_class.model_fields:
                if field.endswith("_id") and field not in self.secure_fields:
                    self.secure_fields.append(field)

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)

    def get_initial_state(self, **kwargs) -> S:
        pk = kwargs.get("pk") or kwargs.get("id")
        if not pk and self.model:
            pk = kwargs.get(f"{self.model.__name__.lower()}_id")

        if pk:
            obj = self.get_object(pk)
            return self.state_class.model_validate(obj)

        if hasattr(self, "state") and hasattr(self.state, "id"):
            obj = self.get_object(self.state.id)
            return self.state_class.model_validate(obj)

        raise ValueError(f"No ID found for {self.model}")

    def refresh(self):
        pk = None
        if hasattr(self.state, "id"):
            pk = self.state.id
        elif hasattr(self.state, f"{self.model.__name__.lower()}_id"):
            pk = getattr(self.state, f"{self.model.__name__.lower()}_id")

        if pk:
            obj = self.get_object(pk)
            new_state = self.state_class.model_validate(obj)
            state_data = self.state.model_dump()
            new_data = new_state.model_dump()
            for key, value in state_data.items():
                if key not in new_data or new_data[key] is None:
                    setattr(new_state, key, value)
                if key in ["editing_id", "edit_buffer", "create_buffer"]:
                    setattr(new_state, key, value)
            self.state = new_state
        else:
            raise ValueError("No ID in state for refresh")


class CrudNitroComponent(ModelNitroComponent[S]):
    """
    Nitro component with built-in CRUD operations.

    Extends ModelNitroComponent with pre-built methods for creating, updating,
    and deleting model instances. Includes edit/create buffer management for
    form handling.

    IMPORTANT: Your state schema MUST use ConfigDict(from_attributes=True)
    when working with Django models. This allows Pydantic to correctly read
    Django model attributes when loading data with model_validate().

    The state schema should include:
        - create_buffer: Optional schema for new item creation
        - edit_buffer: Optional schema for editing existing items
        - editing_id: Optional int for tracking which item is being edited
    """

    def create_item(self):
        """
        Create a new model instance from the create_buffer in state.

        Note: This method does not add success/error messages automatically.
        Override this method in your component to add custom messages.
        """
        if not hasattr(self.state, "create_buffer") or not self.state.create_buffer:
            return

        # Get data from buffer, excluding id but including all other fields
        data = self.state.create_buffer.model_dump(exclude={"id"})

        # Log what we received for debugging
        logger.debug("create_item called on %s with data: %s", self.__class__.__name__, data)

        # Validate that at least one non-empty string field exists
        # (more lenient validation - just check for non-empty strings)
        string_fields = {
            k: v for k, v in data.items() if isinstance(v, str) and not k.endswith("_id")
        }
        has_content = any(v.strip() for v in string_fields.values() if v)

        if not has_content and string_fields:
            logger.debug("Validation failed: no non-empty string fields found in %s", string_fields)
            return

        # Add property_id if this is a related model
        if hasattr(self.state, "property_id"):
            data["property_id"] = self.state.property_id

        try:
            created_obj = self.model.objects.create(**data)
            logger.info("Successfully created %s with id %s", self.model.__name__, created_obj.pk)
            self.state.create_buffer = self.state.create_buffer.__class__()
            self.refresh()
        except Exception as e:
            logger.exception("Error creating %s: %s", self.model.__name__, str(e))
            raise

    def delete_item(self, id: int):
        """
        Delete a model instance by ID.

        Args:
            id: Primary key of the instance to delete

        Note: This method does not add success/error messages automatically.
        Override this method in your component to add custom messages.
        """
        self.model.objects.filter(id=id).delete()
        self.refresh()

    def start_edit(self, id: int):
        """
        Start editing an existing model instance.

        Loads the instance into edit_buffer and sets editing_id.
        Attempts to auto-infer the buffer type from state class annotations.

        Args:
            id: Primary key of the instance to edit
        """
        obj = self.model.objects.get(id=id)
        self.state.editing_id = id

        # Try to infer buffer type from edit_buffer field annotation
        buffer_type = None
        field = self.state_class.model_fields.get("edit_buffer")

        if field and field.annotation:
            try:
                # Extract type from Optional[Schema] (which is Union[Schema, None])
                args = get_args(field.annotation)
                if args:
                    # Get first arg (the actual type, not None)
                    buffer_type = (
                        args[0]
                        if args[0] is not type(None)
                        else (args[1] if len(args) > 1 else None)
                    )
            except (TypeError, AttributeError, IndexError) as e:
                logger.debug(
                    "Could not infer edit_buffer type from annotation for %s: %s",
                    self.__class__.__name__,
                    str(e),
                )

        # Fallback: try to use create_buffer's type if available
        if not buffer_type and hasattr(self.state, "create_buffer"):
            buffer_type = type(self.state.create_buffer)
            logger.debug(
                "Using create_buffer type as fallback for edit_buffer in %s",
                self.__class__.__name__,
            )

        if buffer_type:
            try:
                self.state.edit_buffer = buffer_type.model_validate(obj)
                logger.debug(
                    "Successfully created edit_buffer for %s with type %s",
                    self.__class__.__name__,
                    buffer_type.__name__,
                )
            except Exception as e:
                logger.error(
                    "Failed to create edit_buffer for %s: %s", self.__class__.__name__, str(e)
                )
                self.state.editing_id = None
                raise
        else:
            logger.error(
                "Could not infer edit_buffer type for component %s. "
                "Please override start_edit() method to set the buffer type explicitly.",
                self.__class__.__name__,
            )
            self.state.editing_id = None
            raise ValueError("Could not infer edit_buffer type")

    def save_edit(self):
        """
        Save changes from edit_buffer to the database.

        Updates the model instance with data from edit_buffer,
        clears the editing state, and refreshes component data.

        Note: This method does not add success/error messages automatically.
        Override this method in your component to add custom messages.
        """
        if self.state.editing_id and self.state.edit_buffer:
            data = self.state.edit_buffer.model_dump(exclude={"id"}, exclude_unset=True)
            self.model.objects.filter(id=self.state.editing_id).update(**data)
            self.state.editing_id = None
            self.state.edit_buffer = None
            self.refresh()

    def cancel_edit(self):
        """Cancel editing and clear the edit buffer."""
        self.state.editing_id = None
        self.state.edit_buffer = None
