"""Gemini status codes."""
import enum
from typing import Union


class StatusCode(enum.Enum):
    INPUT = 10

    SUCCESS = 20
    SUCCES_END_OF_CLIENT_CERTIFICATE_SESSION = 21

    REDIRECT_TEMPORARY = 30
    REDIRECT_PERMANENT = 31

    TEMPORARY_FAILURE = 40
    SERVER_UNAVAILABLE = 41
    CGI_ERROR = 42
    PROXY_ERROR = 43
    SLOW_DOWN = 44

    PERMANENT_FAILURE = 50
    NOT_FOUND = 51
    GONE = 52
    PROXY_REQUEST_REFUSED = 53
    BAD_REQUEST = 59

    CLIENT_CERTIFICATE_REQUIRED = 60
    TRANSIENT_CERTIFICATE_REQUIRED = 61
    AUTHORIZED_CERTIFICATE_REQUIRED = 62
    CERTIFICATE_NOT_ACCEPTED = 63
    FUTURE_CERTIFICATE_REJECTED = 64
    EXPIRED_CERTIFICATE_REJECTED = 65


def is_success(code: Union[int, StatusCode]):
    if isinstance(code, int):
        code = StatusCode(code)

    return code.value >= 20 and code.value <= 29