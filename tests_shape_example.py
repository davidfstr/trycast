from typing import List, Literal, Optional  # noqa: F401
from typing import TypedDict as RichTypedDict
from typing import Union, cast  # noqa: F401

from trycast import trycast


class Point2D(RichTypedDict):
    x: float  # also accepts int values parsed by json.loads()
    y: float


class Circle(RichTypedDict):
    type: Literal["circle"]
    center: Point2D  # has a nested TypedDict!
    radius: float


class Rect(RichTypedDict):
    type: Literal["rect"]
    x: float
    y: float
    width: float
    height: float


Shape = Union[Circle, Rect]  # a Tagged Union

shapes_drawn = []  # type: List[Union[Shape, ValueError]]

HTTP_400_BAD_REQUEST = ValueError("HTTP 400: Bad Request")


def draw_shape_endpoint(request_json: object) -> None:
    # TODO: Eliminate need to use cast() here
    shape = cast(Optional[Shape], trycast(Shape, request_json))
    if shape is not None:
        draw_shape(shape)
    else:
        shapes_drawn.append(HTTP_400_BAD_REQUEST)


def draw_shape(shape: Shape) -> None:
    shapes_drawn.append(shape)
