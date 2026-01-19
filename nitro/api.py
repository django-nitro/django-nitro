import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpRequest
from ninja import File, Form, NinjaAPI, Schema
from ninja.files import UploadedFile
from pydantic import ValidationError as PydanticValidationError

from .registry import get_component_class

logger = logging.getLogger(__name__)

# =============================================================================
# Django Ninja API Configuration
# =============================================================================
# Nitro uses Django Ninja for its API layer, providing:
# - Automatic request/response validation with Pydantic schemas
# - OpenAPI/Swagger documentation at /api/nitro/docs
# - Type-safe file uploads with Form[Schema] + File[UploadedFile]
# - Custom exception handlers for consistent error responses
# =============================================================================

api = NinjaAPI(
    urls_namespace="nitro",
    title="Nitro Component API",
    version="0.7.0",
    description="Django Nitro reactive component dispatch API. "
                "Handles actions, state updates, and file uploads for Nitro components.",
)


# =============================================================================
# Request Schemas - Automatic validation with Pydantic
# =============================================================================

class ActionPayload(Schema):
    """Schema for Nitro action dispatch requests (JSON body)."""
    component_name: str
    action: str
    state: dict
    payload: dict = {}
    integrity: str | None = None


class ActionFormPayload(Schema):
    """Schema for form-based requests (multipart/form-data with file uploads)."""
    component_name: str
    action: str
    state: str  # JSON string, parsed later
    payload: str = "{}"  # JSON string, parsed later
    integrity: str = ""


# =============================================================================
# Response Schemas - Type-safe API responses
# =============================================================================

class ErrorResponse(Schema):
    """Standard error response schema."""
    error: str
    detail: str | None = None


class NitroResponse(Schema):
    """Standard Nitro action response schema."""
    html: str | None = None
    state: dict | None = None
    redirect: str | None = None
    error: str | None = None


# =============================================================================
# Exception Handlers - Consistent error responses using Django Ninja
# =============================================================================

@api.exception_handler(PermissionDenied)
def permission_denied_handler(request: HttpRequest, exc: PermissionDenied):
    """Handle Django PermissionDenied exceptions."""
    logger.warning(
        "Permission denied (user: %s, IP: %s): %s",
        getattr(request.user, "username", "anonymous"),
        request.META.get("REMOTE_ADDR"),
        str(exc),
    )
    return api.create_response(
        request,
        {"error": "Permission denied", "detail": str(exc) if settings.DEBUG else None},
        status=403
    )


@api.exception_handler(DjangoValidationError)
def django_validation_handler(request: HttpRequest, exc: DjangoValidationError):
    """Handle Django ValidationError exceptions."""
    logger.warning("Django validation error: %s", str(exc), exc_info=True)
    return api.create_response(
        request,
        {"error": str(exc) if settings.DEBUG else "Validation error"},
        status=400
    )


@api.exception_handler(PydanticValidationError)
def pydantic_validation_handler(request: HttpRequest, exc: PydanticValidationError):
    """Handle Pydantic ValidationError exceptions."""
    logger.warning("Pydantic validation error: %s", str(exc), exc_info=True)
    return api.create_response(
        request,
        {"error": str(exc) if settings.DEBUG else "Invalid request data"},
        status=400
    )


# =============================================================================
# API Endpoints
# =============================================================================

# Standard JSON endpoint - uses Ninja's schema validation
@api.post("/dispatch")
def nitro_dispatch(request: HttpRequest, data: ActionPayload):
    """Handle standard JSON Nitro action dispatch."""
    return _process_dispatch(
        request=request,
        comp_name=data.component_name,
        act=data.action,
        state_dict=data.state,
        payload_dict=data.payload,
        integ=data.integrity or "",
        file=None
    )


# File upload endpoint - uses Form + File for multipart/form-data
@api.post("/dispatch-file")
def nitro_dispatch_file(
    request: HttpRequest,
    data: Form[ActionFormPayload],
    file: File[UploadedFile] = None
):
    """Handle Nitro action dispatch with file upload."""
    # Parse JSON strings from form data
    try:
        state_dict = json.loads(data.state) if data.state else {}
        payload_dict = json.loads(data.payload) if data.payload else {}
    except json.JSONDecodeError:
        return api.create_response(request, {"error": "Invalid JSON in form data"}, status=400)

    return _process_dispatch(
        request=request,
        comp_name=data.component_name,
        act=data.action,
        state_dict=state_dict,
        payload_dict=payload_dict,
        integ=data.integrity,
        file=file
    )


# =============================================================================
# Core Dispatch Logic
# =============================================================================

def _process_dispatch(
    request: HttpRequest,
    comp_name: str,
    act: str,
    state_dict: dict,
    payload_dict: dict,
    integ: str,
    file: UploadedFile | None
):
    """
    Common dispatch logic for both JSON and file upload endpoints.

    This is the core Nitro dispatch handler that:
    1. Finds the component class from the registry
    2. Verifies security integrity (HMAC signature)
    3. Processes the action via component.process_action()
    4. Returns the response (HTML + updated state)

    Note: PermissionDenied, DjangoValidationError, and PydanticValidationError
    are handled by Django Ninja's exception handlers defined above.
    """
    ComponentClass = get_component_class(comp_name)
    if not ComponentClass:
        logger.warning(
            "Component not found: %s (from IP: %s)", comp_name, request.META.get("REMOTE_ADDR")
        )
        return api.create_response(request, {"error": "Component not found"}, status=404)

    try:
        component_instance = ComponentClass(request=request, initial_state=state_dict)

        # Verify security integrity (HMAC signature validation)
        if not component_instance.verify_integrity(integ):
            logger.warning(
                "Integrity check failed for component %s (action: %s, IP: %s)",
                comp_name,
                act,
                request.META.get("REMOTE_ADDR"),
            )
            return api.create_response(
                request, {"error": "Security verification failed"}, status=403
            )

        # Process the action - exceptions bubble up to global handlers
        response_data = component_instance.process_action(
            action_name=act,
            payload=payload_dict,
            current_state_dict=state_dict,
            uploaded_file=file,
        )
        return response_data

    except (PermissionDenied, DjangoValidationError, PydanticValidationError):
        # Let Django Ninja's exception handlers deal with these
        raise

    except ValueError as e:
        # ValueError isn't caught by global handlers, handle inline
        logger.warning(
            "ValueError in component %s action %s: %s",
            comp_name, act, str(e), exc_info=True
        )
        error_detail = str(e) if settings.DEBUG else "Invalid request data"
        return api.create_response(request, {"error": error_detail}, status=400)

    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception("Unexpected error in component %s action %s: %s", comp_name, act, str(e))
        return api.create_response(
            request, {"error": "An unexpected error occurred. Please try again later."}, status=500
        )
