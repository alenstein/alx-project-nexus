import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    PermissionDenied,
    MethodNotAllowed,
    NotFound
)

# Get an instance of a logger for this module
logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    A custom exception handler for the entire DRF project.

    This handler ensures that all API errors, whether client-side (4xx) or
    server-side (5xx), are returned in a consistent JSON format:
    {
        "errors": { ... }
    }
    """
    # Let DRF's default handler process the exception first.
    # This gives us a baseline response with the correct status code.
    response = exception_handler(exc, context)

    # Prepare a standardized error payload.
    error_payload = {
        "errors": {}
    }

    # --- Handle Specific DRF Exceptions ---

    if isinstance(exc, ValidationError):
        # For validation errors, the details are already well-structured.
        error_payload["errors"] = exc.detail
        return Response(error_payload, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, (AuthenticationFailed, PermissionDenied)):
        # For authentication and permission errors, provide a clear 'detail' message.
        error_payload["errors"] = {'detail': exc.detail}
        return Response(error_payload, status=exc.status_code)

    if isinstance(exc, (NotFound, Http404)):
        # For any "not found" errors, log it as a warning and return a standard message.
        logger.warning(f"404 Not Found: {context['request'].path}")
        error_payload["errors"] = {'detail': 'The requested resource was not found.'}
        return Response(error_payload, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, MethodNotAllowed):
        # For method not allowed errors.
        logger.warning(f"405 Method Not Allowed: {context['request'].method} on {context['request'].path}")
        error_payload["errors"] = {'detail': f'Method "{context["request"].method}" not allowed.'}
        return Response(error_payload, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    # --- Handle Generic DRF Responses and Unhandled Server Errors ---

    if response is not None:
        # If DRF provided a response, we use its status code but format the data.
        # This catches other generic DRF errors.
        error_payload["errors"] = {'detail': response.data.get('detail', 'An error occurred.')}
        return Response(error_payload, status=response.status_code)

    # For all other unhandled exceptions, this is a 500 server error.
    # Log the full exception traceback for debugging purposes.
    logger.error(
        f"Unhandled exception caught: {exc} at path {context['request'].path}",
        exc_info=True
    )
    
    # Return a generic, non-revealing server error message to the user.
    error_payload["errors"] = {'detail': 'A server error occurred. Please try again later.'}
    return Response(error_payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
