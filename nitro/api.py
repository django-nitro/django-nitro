import logging
import json
from ninja import NinjaAPI, Schema, File, Form
from ninja.files import UploadedFile
from django.http import HttpRequest
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import ValidationError as PydanticValidationError
from .registry import get_component_class
from typing import Optional

logger = logging.getLogger(__name__)
api = NinjaAPI(urls_namespace='nitro')

class ActionPayload(Schema):
    component_name: str
    action: str
    state: dict
    payload: dict = {}
    integrity: Optional[str] = None # <--- INDISPENSABLE

@api.post("/dispatch")
def nitro_dispatch(request: HttpRequest):
    # Detect request type based on Content-Type header
    is_formdata = request.content_type and 'multipart/form-data' in request.content_type

    if is_formdata:
        # FormData request (with file upload)
        comp_name = request.POST.get('component_name')
        act = request.POST.get('action')
        state_dict = json.loads(request.POST.get('state', '{}'))
        payload_dict = json.loads(request.POST.get('payload', '{}'))
        integ = request.POST.get('integrity', '')
        file = request.FILES.get('file', None)
    else:
        # Standard JSON request
        try:
            body = json.loads(request.body)
            comp_name = body.get('component_name')
            act = body.get('action')
            state_dict = body.get('state', {})
            payload_dict = body.get('payload', {})
            integ = body.get('integrity', '')
            file = None
        except json.JSONDecodeError:
            return api.create_response(request, {"error": "Invalid JSON"}, status=400)

    ComponentClass = get_component_class(comp_name)
    if not ComponentClass:
        logger.warning(
            "Component not found: %s (from IP: %s)",
            comp_name,
            request.META.get('REMOTE_ADDR')
        )
        return api.create_response(request, {"error": "Component not found"}, status=404)

    try:
        component_instance = ComponentClass(request=request, initial_state=state_dict)

        # Verify security integrity
        if not component_instance.verify_integrity(integ):
            logger.warning(
                "Integrity check failed for component %s (action: %s, IP: %s)",
                comp_name,
                act,
                request.META.get('REMOTE_ADDR')
            )
            return api.create_response(
                request,
                {"error": "Security verification failed"},
                status=403
            )

        response_data = component_instance.process_action(
            action_name=act,
            payload=payload_dict,
            current_state_dict=state_dict,
            uploaded_file=file  # Pass the file (None if not present)
        )
        return response_data

    except PermissionDenied as e:
        logger.warning(
            "Permission denied for component %s action %s: %s (user: %s)",
            comp_name,
            act,
            str(e),
            getattr(request.user, 'username', 'anonymous')
        )
        return api.create_response(
            request,
            {"error": "Permission denied"},
            status=403
        )

    except (ValueError, DjangoValidationError, PydanticValidationError) as e:
        logger.warning(
            "Validation error in component %s action %s: %s",
            comp_name,
            act,
            str(e),
            exc_info=True  # Include full traceback
        )
        # In development, return detailed error; in production, use generic message
        from django.conf import settings
        error_detail = str(e) if settings.DEBUG else "Invalid request data"
        return api.create_response(
            request,
            {"error": error_detail},
            status=400
        )

    except Exception as e:
        logger.exception(
            "Unexpected error in component %s action %s: %s",
            comp_name,
            act,
            str(e)
        )
        return api.create_response(
            request,
            {"error": "An unexpected error occurred. Please try again later."},
            status=500
        )