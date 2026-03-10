import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error response formatting
    and converts Django ValidationErrors to DRF ValidationErrors.
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        else:
            exc = DRFValidationError(detail=exc.messages)

    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            "success": False,
            "status_code": response.status_code,
            "errors": [],
        }

        if isinstance(response.data, dict):
            for field, value in response.data.items():
                if isinstance(value, list):
                    for item in value:
                        custom_response_data["errors"].append(
                            {"field": field, "message": str(item)}
                        )
                else:
                    custom_response_data["errors"].append(
                        {"field": field, "message": str(value)}
                    )
        elif isinstance(response.data, list):
            for item in response.data:
                custom_response_data["errors"].append(
                    {"field": "non_field_error", "message": str(item)}
                )
        else:
            custom_response_data["errors"].append(
                {"field": "detail", "message": str(response.data)}
            )

        response.data = custom_response_data
    else:
        # Unhandled exceptions -- log and return generic 500
        logger.exception("Unhandled exception in API view", exc_info=exc)
        response = Response(
            {
                "success": False,
                "status_code": 500,
                "errors": [
                    {
                        "field": "server",
                        "message": "An unexpected error occurred. Please try again later.",
                    }
                ],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
