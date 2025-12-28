import json
import logging
from typing import TypeVar, Generic, Type, Dict, List, Optional, get_args
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from django.core.signing import Signer, BadSignature
from django.http import HttpRequest
from django.db import models
from pydantic import BaseModel

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
    """
    template_name: str = ""
    component_id: str = ""
    state_class: Optional[Type[S]] = None
    state: S
    secure_fields: List[str] = [] 

    def __init__(self, request: Optional[HttpRequest] = None, initial_state: dict = None, **kwargs):
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
        self._pending_errors: Dict[str, str] = {}
        self._pending_messages: List[Dict[str, str]] = []

        if initial_state is not None:
            if self.state_class:
                self.state = self.state_class(**initial_state)
            else:
                self.state = initial_state # type: ignore
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

    def _compute_integrity(self) -> str:
        """
        Compute an integrity token for secure fields.

        Creates an HMAC-based signature of the values in secure_fields
        to prevent client-side tampering.

        Returns:
            A signed token string, or empty string if no secure fields are defined
        """
        if not self.secure_fields: return ""
        state_dump = self.state.model_dump() if hasattr(self.state, 'model_dump') else self.state
        data_to_sign = "|".join([f"{k}:{state_dump.get(k)}" for k in self.secure_fields])
        return self._signer.sign(data_to_sign)

    def verify_integrity(self, token: Optional[str]) -> bool:
        """
        Verify that secure fields haven't been tampered with.

        Compares the provided integrity token against the current state
        to ensure data integrity.

        Args:
            token: The integrity token from the client

        Returns:
            True if verification passes or no secure fields exist, False otherwise
        """
        if not self.secure_fields: return True
        if not token: return False
        try:
            original_data = self._signer.unsign(token)
            state_dump = self.state.model_dump() if hasattr(self.state, 'model_dump') else self.state
            current_data = "|".join([f"{k}:{state_dump.get(k)}" for k in self.secure_fields])
            return original_data == current_data
        except BadSignature:
            return False

    def add_error(self, field: str, message: str):
        """Add a field-specific validation error to be sent to the client."""
        self._pending_errors[field] = message

    def success(self, message: str):
        """Add a success message to be displayed to the user."""
        self._pending_messages.append({"level": "success", "text": message})

    def error(self, message: str):
        """Add an error message to be displayed to the user."""
        self._pending_messages.append({"level": "error", "text": message})

    def render(self):
        """
        Render the component as HTML with embedded AlpineJS state.

        Creates a wrapper div with x-data directive containing the component's
        state, errors, messages, and integrity token. The template is rendered
        inside this wrapper.

        Returns:
            SafeString containing the complete HTML for the component
        """
        state_dict = self.state.model_dump() if hasattr(self.state, 'model_dump') else self.state

        # Package everything for the JavaScript layer
        full_payload = {
            "state": state_dict,
            "errors": {},
            "messages": [],
            "integrity": self._compute_integrity()
        }

        context = {"state": state_dict, "component": self}
        if self.request: context['request'] = self.request

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

    def process_action(self, action_name: str, payload: dict, current_state_dict: dict, uploaded_file=None):
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
            Dictionary containing updated state, errors, messages, and integrity token

        Raises:
            ValueError: If the action method doesn't exist on this component
        """
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
                exc_info=True
            )
            raise

        if hasattr(self, action_name):
            action_method = getattr(self, action_name)

            # Check if action accepts uploaded_file parameter
            import inspect
            sig = inspect.signature(action_method)
            if 'uploaded_file' in sig.parameters:
                action_method(**payload, uploaded_file=uploaded_file)
            else:
                action_method(**payload)

            return {
                "state": self.state.model_dump() if hasattr(self.state, 'model_dump') else self.state,
                "errors": self._pending_errors,
                "messages": self._pending_messages,
                "integrity": self._compute_integrity()
            }
        raise ValueError(f"Action {action_name} not found")

class ModelNitroComponent(NitroComponent[S]):
    """
    Nitro component with Django ORM integration.

    Extends NitroComponent with automatic model loading, queryset support,
    and automatic secure field detection for database IDs and foreign keys.

    Attributes:
        model: Django model class associated with this component
    """
    model: Optional[Type[models.Model]] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model:
            if 'id' in self.state_class.model_fields: self.secure_fields.append('id')
            for field in self.state_class.model_fields:
                if field.endswith("_id") and field not in self.secure_fields:
                     self.secure_fields.append(field)

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)

    def get_initial_state(self, **kwargs) -> S:
        pk = kwargs.get('pk') or kwargs.get('id')
        if not pk and self.model:
            pk = kwargs.get(f"{self.model.__name__.lower()}_id")

        if pk:
            obj = self.get_object(pk)
            return self.state_class.model_validate(obj)
        
        if hasattr(self, 'state') and hasattr(self.state, 'id'):
             obj = self.get_object(self.state.id)
             return self.state_class.model_validate(obj)

        raise ValueError(f"No ID found for {self.model}")

    def refresh(self):
        pk = None
        if hasattr(self.state, 'id'): pk = self.state.id
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
                if key in ['editing_id', 'edit_buffer', 'create_buffer']:
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
        if not hasattr(self.state, 'create_buffer') or not self.state.create_buffer:
            return

        # Get data from buffer, excluding id but including all other fields
        data = self.state.create_buffer.model_dump(exclude={'id'})

        # Log what we received for debugging
        logger.debug(
            "create_item called on %s with data: %s",
            self.__class__.__name__,
            data
        )

        # Validate that at least one non-empty string field exists
        # (more lenient validation - just check for non-empty strings)
        string_fields = {k: v for k, v in data.items() if isinstance(v, str) and not k.endswith('_id')}
        has_content = any(v.strip() for v in string_fields.values() if v)

        if not has_content and string_fields:
            logger.debug("Validation failed: no non-empty string fields found in %s", string_fields)
            return

        # Add property_id if this is a related model
        if hasattr(self.state, 'property_id'):
            data['property_id'] = self.state.property_id

        try:
            created_obj = self.model.objects.create(**data)
            logger.info(
                "Successfully created %s with id %s",
                self.model.__name__,
                created_obj.pk
            )
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
        field = self.state_class.model_fields.get('edit_buffer')

        if field and field.annotation:
            try:
                # Extract type from Optional[Schema] (which is Union[Schema, None])
                args = get_args(field.annotation)
                if args:
                    # Get first arg (the actual type, not None)
                    buffer_type = args[0] if args[0] is not type(None) else (args[1] if len(args) > 1 else None)
            except (TypeError, AttributeError, IndexError) as e:
                logger.debug(
                    "Could not infer edit_buffer type from annotation for %s: %s",
                    self.__class__.__name__, str(e)
                )

        # Fallback: try to use create_buffer's type if available
        if not buffer_type and hasattr(self.state, 'create_buffer'):
            buffer_type = type(self.state.create_buffer)
            logger.debug(
                "Using create_buffer type as fallback for edit_buffer in %s",
                self.__class__.__name__
            )

        if buffer_type:
            try:
                self.state.edit_buffer = buffer_type.model_validate(obj)
                logger.debug(
                    "Successfully created edit_buffer for %s with type %s",
                    self.__class__.__name__, buffer_type.__name__
                )
            except Exception as e:
                logger.error(
                    "Failed to create edit_buffer for %s: %s",
                    self.__class__.__name__, str(e)
                )
                self.state.editing_id = None
                raise
        else:
            logger.error(
                "Could not infer edit_buffer type for component %s. "
                "Please override start_edit() method to set the buffer type explicitly.",
                self.__class__.__name__
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
            data = self.state.edit_buffer.model_dump(exclude={'id'}, exclude_unset=True)
            self.model.objects.filter(id=self.state.editing_id).update(**data)
            self.state.editing_id = None
            self.state.edit_buffer = None
            self.refresh()

    def cancel_edit(self):
        """Cancel editing and clear the edit buffer."""
        self.state.editing_id = None
        self.state.edit_buffer = None