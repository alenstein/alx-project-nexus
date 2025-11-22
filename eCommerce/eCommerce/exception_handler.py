import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import ValidationError, AuthenticationFailed, PermissionDenied

# Get an instance of a logger
logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    This handler returns a standardized JSON response for all API errors.
    """
    # First, call DRF's default exception handler to get the standard error response.
    response = exception_handler(exc, context)

    # Prepare a standardized error structure
    error_payload = {
        "errors": {}
    }

    if isinstance(exc, ValidationError):
        # For validation errors, the details are in exc.detail
        error_payload["errors"] = exc.detail
        return Response(error_payload, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, (AuthenticationFailed, PermissionDenied)):
        # For auth errors, provide a clear message
        error_payload["errors"] = {'detail': exc.detail}
        return Response(error_payload, status=exc.status_code)

    if isinstance(exc, Http404):
        # For 404 errors
        error_payload["errors"] = {'detail': 'The requested resource was not found.'}
        return Response(error_payload, status=status.HTTP_404_NOT_FOUND)

    # If the default handler provided a response, use its data
    if response is not None:
        error_payload["errors"] = {'detail': response.data.get('detail', 'An error occurred.')}
        return Response(error_payload, status=response.status_code)

    # For all other unhandled exceptions, this is a 500 server error.
    # Log the full exception for debugging.
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return a generic server error message to the user.
    error_payload["errors"] = {'detail': 'A server error occurred. Please try again later.'}
    return Response(error_payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
