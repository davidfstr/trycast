# trycast

trycast parses JSON-like values whose shape is defined by
[typed dictionaries](https://www.python.org/dev/peps/pep-0589/#abstract)
(TypedDicts) and other standard Python type hints.

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
    ...
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
> in the example so that it is accepted by the typechecker without complaining:
> 
> ```python
> shape = cast(Optional[Shape], trycast(Shape, request_json))
> if shape is not None:
>     ...
> ```
> 
> These limitations are in the process of being resolved by
> [introducing TypeForm support to mypy](https://github.com/python/mypy/issues/9773).


## Motivation & Alternatives

Why use typed dictionaries to represent data structures instead of classes,
named tuples, or other formats?

Typed dictionaries are the natural form that JSON data comes in over the wire.
They can be trivially serialized and deserialized without any additional logic.
For applications that use a lot of JSON data - such as web applications - 
using typed dictionaries is very convenient for representing data structures.

Other alternatives for representing data structures in Python include
[dataclasses], [named tuples], [attrs], and plain classes.

[dataclasses]: https://www.python.org/dev/peps/pep-0557/#abstract
[named tuples]: https://docs.python.org/3/library/typing.html#typing.NamedTuple
[attrs]: https://www.attrs.org/en/stable/


## Recommendations while using trycast

- So that `trycast()` can recognize TypedDicts with mixed required and
  optional keys correctly:
    * Use Python 3.9+ if possible.
    * Prefer using `typing.TypedDict`, unless you must use Python 3.8.
      In Python 3.8 prefer `typing_extensions.TypedDict` instead.
    * Avoid using `mypy_extensions.TypedDict` in general.


# License

[MIT](LICENSE.md)


## Changelog

### Future

* See the [Roadmap](https://github.com/davidfstr/trycast/wiki/Roadmap).

### master

* Setup continuous integration with GitHub Actions.

### v0.3.0

* TypedDict improvements & fixes:
    * Fix `trycast()` to recognize custom Mapping subclasses as TypedDicts.
* Extend `trycast()` to recognize more JSON-like values:
    * Extend `trycast()` to recognize `Mapping` and `MutableMapping` values.
    * Extend `trycast()` to recognize `tuple[T, ...]` and `Tuple[T, ...]` values.
    * Extend `trycast()` to recognize `Sequence` and `MutableSequence` values.
* Extend `trycast()` to recognize `tuple[T1, T2, etc]` and `Tuple[T1, T2, etc]` values.
* Documentation improvements:
    * Improve introduction.
    * Outline motivation to use trycast and note alternatives.

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
