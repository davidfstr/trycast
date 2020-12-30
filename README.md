# trycast

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

> **Important:** Current limitations in the mypy typechecker require that you
> add an extra `cast(Optional[Shape], ...)` around the call to `trycast`
> in the example so that it is accepted by the typechecker without complaining.
> These limitations are in the process of being resolved by
> [introducing TypeForm support to mypy](https://github.com/python/mypy/issues/9773).


## Recommendations when using trycast

- So that `trycast()` can recognize TypedDicts with mixed required and
  optional keys correctly:
    * Use Python 3.9+ if possible.
    * Prefer using `typing.TypedDict`, unless you must use Python 3.8.
      In Python 3.8 prefer `typing_extensions.TypedDict` instead.
    * Avoid using `mypy_extensions.TypedDict` in general.


## Release Notes

### Future

* See the [Roadmap](https://github.com/davidfstr/trycast/wiki/Roadmap).

### v0.2.0

* TypedDict improvements & fixes:
    * Fix `trycast()` to recognize TypedDicts from `mypy_extensions`.
    * Extend `trycast()` to recognize TypedDicts that contain forward-references
      to other types.
        - Unfortunately there appears to be no easy way to support arbitrary kinds
          of types that contain forward-references.
        - In particular {Union, Optional} types and collection types (List, Dict)
          with forward-references remain unsupported by `trycast()`.
    * Recognize TypedDicts that have mixed required and optional keys correctly.
        - Exception: Does not work for mypy_extensions.TypedDict or
          Python 3.8's typing.TypedDict due to insufficient runtime
          type annotation information.
    * Fix recognition of a total=False TypedDict so that extra keys are disallowed.
* Alter `typing_extensions` to be an optional dependency of `trycast`.

### v0.1.0

* Add support for Python 3.6, 3.7, and 3.9, in addition to 3.8.

### v0.0.2

* Fix README to appear on PyPI.
* Add other package metadata, such as the supported Python versions.

### v0.0.1

* Initial release.
* Supports typechecking all types found in JSON.
