from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError, APIException
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exception, context):
    """
    Custom exception handler adds handling django model exceptions to django rest framework
    :return:
    """
    if isinstance(exception, DjangoValidationError):
        if hasattr(exception, 'message_dict'):
            detail = exception.message_dict
        elif hasattr(exception, 'message'):
            detail = exception.message
        elif hasattr(exception, 'messages'):
            detail = exception.messages
        exception = DRFValidationError(detail=detail)
    # elif not isinstance(exception, APIException):
    #     print(exception)
    return drf_exception_handler(exception, context)
