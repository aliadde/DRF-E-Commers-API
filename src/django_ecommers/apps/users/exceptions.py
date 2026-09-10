"""custome exceptions"""

from rest_framework.exceptions import APIException


class DuplicateHTTPException(APIException):
    status_code = 409
    default_detail = "The name or email you provided is already taken."
    default_code = "duplicate"
