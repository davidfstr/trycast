# trycast

> **Status:** In development. Current limitations in mypy prevent the examples
> below from actually typechecking successfully, despite functioning correctly
> at runtime.

This module provides a single function `trycast` which can be used to parse a
JSON-like value.

Here is an example of parsing a `Point2D` object defined as a `TypedDict`:

```python
from bottle import HTTPResponse, request, route
from trycast import trycast
from typing import TypedDict

class Point2D(TypedDict):
    x: float
    y: float
    name: str

@route('/draw_point')
def draw_point_endpoint() -> None:
    request_json = request.json  # type: object
    if (point := trycast(Point2D, request_json)) is not None:
        draw_point(point)  # type is narrowed to Point2D
    else:
        return HTTPResponse(status=400)  # Bad Request

def draw_point(point: Point2D) -> None:
    # ...
```

In this example the `trycast` function is asked to parse a `request_json`
into a `Point2D` object, returning the original object (with its type narrowed
appropriately) if parsing was successful.

More complex types can be parsed as well, such as the `Shape` in the following
example, which is a tagged union that can be either a `Circle` or `Rect` value:

```python
from bottle import HTTPResponse, request, route
from trycast import trycast
from typing import Literal, TypedDict, Union

class Point2D(TypedDict):
    x: float
    y: float

class Circle(TypedDict):
    type: Literal['circle']
    center: Point2D  # a nested TypedDict!
    radius: float

class Rect(TypedDict):
    type: Literal['rect']
    x: float
    y: float
    width: float
    height: float

Shape = Union[Circle, Rect]  # a Tagged Union!

@route('/draw_shape')
def draw_shape_endpoint() -> None:
    request_json = request.json  # type: object
    if (shape := trycast(Shape, request_json)) is not None:
        draw_shape(shape)  # type is narrowed to Shape
    else:
        return HTTPResponse(status=400)  # Bad Request
```
