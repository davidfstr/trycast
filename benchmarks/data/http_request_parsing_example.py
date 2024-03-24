import sys
from typing import Literal, Mapping, Optional

# RichTypedDict
if sys.version_info >= (3, 9):
    # Python 3.9+
    from typing import (
        TypedDict as RichTypedDict,  # type: ignore[not-supported-yet]  # pytype
    )
else:
    # Python 3.8+
    from typing_extensions import (
        TypedDict as RichTypedDict,  # type: ignore[not-supported-yet]  # pytype
    )


# For test_http_request_parsing_example
class _ProxiedHttpRequestEnvelope(RichTypedDict):
    request: "_ProxiedHttpRequest"


class _ProxiedHttpRequest(RichTypedDict):
    url: str
    method: "_ProxiedHttpMethod"  # type: ignore[98]  # pyre
    headers: Mapping[str, str]
    content: "_ProxiedHttpContent"


_ProxiedHttpMethod = Literal[
    "DELETE",
    "GET",
    "HEAD",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]


class _ProxiedHttpContent(RichTypedDict):
    type: Optional["_HttpContentTypeDescriptor"]  # None only if text == ''
    text: str


class _HttpContentTypeDescriptor(RichTypedDict):
    family: "_HttpContentTypeFamily"  # type: ignore[6]  # pyre
    value: "_HttpContentType"  # type: ignore[6]  # pyre


_HttpContentTypeFamily = Literal[
    "text/plain",
    "text/html",
    "x-www-form-urlencoded",
    "application/json",
]

_HttpContentType = str
