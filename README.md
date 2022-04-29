# trycast

<img src="https://raw.githubusercontent.com/davidfstr/trycast/main/README/trycast-logo.png" title="trycast logo" align="right" />

Trycast helps parses JSON-like values whose shape is defined by
[typed dictionaries](https://www.python.org/dev/peps/pep-0589/#abstract)
(TypedDicts) and other standard Python type hints.

You can use either the `trycast()` or `isassignable()` functions below
for parsing:


### trycast()

Here is an example of parsing a `Point2D` object defined as a `TypedDict`
using `trycast()`:

```python
from bottle import HTTPResponse, request, route
from trycast import trycast
from typing import TypedDict

class Point2D(TypedDict):
    x: float
    y: float
    name: str

@route('/draw_point')
def draw_point_endpoint() -> HTTPResponse:
    request_json = request.json  # type: object
    if (point := trycast(Point2D, request_json)) is not None:
        draw_point(point)  # type is narrowed to Point2D
        return HTTPResponse(status=200)
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
from typing import Literal, TypedDict

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

Shape = Circle | Rect  # a Tagged Union!

@route('/draw_shape')
def draw_shape_endpoint() -> HTTPResponse:
    request_json = request.json  # type: object
    if (shape := trycast(Shape, request_json)) is not None:
        draw_shape(shape)  # type is narrowed to Shape
        return HTTPResponse(status=200)  # OK
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


### isassignable()

Here is an example of parsing a `Shape` object defined as a union of
`TypedDict`s using `isassignable()`:

```python
class Circle(TypedDict):
    type: Literal['circle']
    ...

class Rect(TypedDict):
    type: Literal['rect']
    ...

Shape = Circle | Rect  # a Tagged Union!

@route('/draw_shape')
def draw_shape_endpoint() -> HTTPResponse:
    request_json = request.json  # type: object
    if isassignable(request_json, Shape):
        draw_shape(request_json)  # type is narrowed to Shape
        return HTTPResponse(status=200)  # OK
    else:
        return HTTPResponse(status=400)  # Bad Request
```

> **Important:** Current limitations in the mypy typechecker prevent the
> automatic narrowing of the type of `request_json` in the above example to
> `Shape`, so you must add an additional `cast()` to narrow the type manually:
> 
> ```python
> if isassignable(request_json, Shape):
>     shape = cast(Shape, request_json)  # type is manually narrowed to Shape
>     draw_shape(shape)
> ```
> 
> These limitations are in the process of being resolved by
> [introducing TypeForm support to mypy](https://github.com/python/mypy/issues/9773).


#### A better `isinstance()`

`isassignable(value, T)` is similar to Python's builtin `isinstance()` but
additionally supports checking against arbitrary type annotation objects
including TypedDicts, Unions, Literals, and many others.

Formally, `isassignable(value, T)` checks whether `value` is consistent with a 
variable of type `T` (using [PEP 484](https://peps.python.org/pep-0484/) static
typechecking rules), but at *runtime*.


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
  not-required keys correctly:
    * Use Python 3.9+ if possible.
    * Prefer using `typing.TypedDict`, unless you must use Python 3.8.
      In Python 3.8 prefer `typing_extensions.TypedDict` instead.
    * Avoid using `mypy_extensions.TypedDict` in general.


## More Information

A presentation about trycast was given at the 2021 PyCon Typing Summit:

[![2021 PyCon Typing Summit Presentation](https://raw.githubusercontent.com/davidfstr/trycast/main/README/TypingSummit2021_Presentation_FirstSlide.png)](https://youtu.be/ld9rwCvGdhc?t=1782)


## License

[MIT](LICENSE.md)


## API Reference

### trycast API

```
def trycast(
    tp: TypeForm[T], 
    value: object,
    /, failure: F = None,
    *, strict: bool = True,
    eval: bool = True
) -> T | F:
```

If `value` is in the shape of `tp` (as accepted by a Python typechecker
conforming to PEP 484 "Type Hints") then returns it, otherwise returns
`failure` (which is None by default).

This method logically performs an operation similar to:

```
return value if isinstance(tp, value) else failure
```

except that it supports many more types than `isinstance`, including:

* List[T]
* Dict[K, V]
* Optional[T]
* Union[T1, T2, ...]
* Literal[...]
* T extends TypedDict

Note that unlike isinstance(), this method does NOT consider bool values
to be valid int values, as consistent with Python typecheckers:

> trycast(int, False) -> None
> isinstance(False, int) -> True

Note that unlike isinstance(), this method considers every int value to
also be a valid float value, as consistent with Python typecheckers:

> trycast(float, 1) -> 1
> isinstance(1, float) -> False

Parameters:

* **strict** -- 
  If strict=False then trycast will additionally accept
  mypy_extensions.TypedDict instances and Python 3.8 typing.TypedDict
  instances for the `tp` parameter. Normally these kinds of types are
  rejected by trycast with a TypeNotSupportedError because these
  types do not preserve enough information at runtime to reliably
  determine which keys are required and which are potentially-missing.
* **eval** --
  If eval=False then trycast will not attempt to resolve string
  type references, which requires the use of the eval() function.
  Otherwise string type references will be accepted.

Raises:

* **TypeNotSupportedError** --
  If strict=True and either mypy_extensions.TypedDict or a
  Python 3.8 typing.TypedDict is found within the `tp` argument.
* **UnresolvedForwardRefError** --
  If `tp` is a type form which contains a ForwardRef.
* **UnresolvableTypeError** --
  If `tp` is a string that could not be resolved to a type.


### isassignable API

```
def isassignable(
    value: object,
    tp: TypeForm[T],
    *, eval: bool = True
) -> TypeGuard[T]:
```

Returns whether `value` is in the shape of `tp`
(as accepted by a Python typechecker conforming to PEP 484 "Type Hints").

This method logically performs an operation similar to:

```
return isinstance(tp, value)
```

except that it supports many more types than `isinstance`, including:

* List[T]
* Dict[K, V]
* Optional[T]
* Union[T1, T2, ...]
* Literal[...]
* T extends TypedDict

Note that unlike isinstance(), this method does NOT consider bool values
to be valid int values, as consistent with Python typecheckers:

> isassignable(False, int) -> False
> isinstance(False, int) -> True

Note that unlike isinstance(), this method considers every int value to
also be a valid float value, as consistent with Python typecheckers:

> isassignable(1, float) -> True
> isinstance(1, float) -> False

Parameters:
* **eval** --
  If eval=False then isassignable will not attempt to resolve string
  type references, which requires the use of the eval() function.
  Otherwise string type references will be accepted.

Raises:
* **TypeNotSupportedError** --
  If mypy_extensions.TypedDict or a
  Python 3.8 typing.TypedDict is found within the `tp` argument.
* **UnresolvedForwardRefError** --
  If `tp` is a type form which contains a ForwardRef.
* **UnresolvableTypeError** --
  If `tp` is a string that could not be resolved to a type.


## Changelog

### Future

* See the [Roadmap](https://github.com/davidfstr/trycast/wiki/Roadmap).

### v0.7.3

* Support X|Y syntax for Union types from 
  [PEP 604](https://peps.python.org/pep-0604/).
* Documentation improvements:
    * Improve introduction.
    * Add API reference.

### v0.7.2

* Add logo.

### v0.7.1

* Upgrade development status from Beta to Production/Stable: 🎉
    * trycast is thoroughly tested.
    * trycast has high code coverage (98%, across Python 3.7-3.10).
    * trycast has been in production use for over a year
      at [at least one company] without issues.
    * trycast supports all major Python type checkers
      (Mypy, Pyright/Pylance, Pyre, Pytype).
    * trycast's initial API is finalized.
* Fix `coverage` to be a dev-dependency rather than a regular dependency.

### v0.7.0

* Finalize the initial API:
    * Alter `trycast()` to use `strict=True` by default rather than
      `strict=False`. **(Breaking change)**
    * Define trycast's `__all__` to export only the
      `trycast` and `isassignable` functions.
* Add support for additional type checkers, in addition to [Mypy]:
    * Add support for the [Pyright] type checker and
      [Pylance] language server extension (for Visual Studio Code).
    * Add support for the [Pyre] type checker.
    * Add support for the [Pytype] type checker.
* Extend `trycast()` to recognize special `Any` and `NoReturn` values.
* Fix `trycast()` to provide better diagnostic error when given a tuple
  of types as its `tp` argument. Was broken in v0.6.0.

[Mypy]: http://mypy-lang.org/
[Pyright]: https://github.com/microsoft/pyright#readme
[Pylance]: https://github.com/microsoft/pylance-release#readme
[Pyre]: https://pyre-check.org/
[Pytype]: https://google.github.io/pytype/

### v0.6.1

* Fix `trycast(..., eval=False)` to not use `typing.get_type_hints()`,
  which internally calls `eval()`.
* Fix `trycast()` and `isassignable()` to avoid swallowing KeyboardInterrupt
  and other non-Exception BaseExceptions.

### v0.6.0

* Extend `trycast()` to recognize a stringified type argument.
* Extend `trycast()` to report a better error message when given
  a type argument with an unresolved forward reference (`ForwardRef`).
* Fix `strict` argument to `trycast` to be passed to inner calls of `trycast`
  correctly.
    * This also fixes `isassignable()`'s use of strict matching to be correct.
* Alter `trycast()` to interpret a type argument of `None` or `"None"` as an
  alias for `type(None)`, as consistent with
  [PEP 484](https://peps.python.org/pep-0484/#using-none).
* Alter `TypeNotSupportedError` to extend `TypeError` rather than `ValueError`.
  **(Breaking change)**
    * This is consistent with `trycast`'s and `isinstance`'s behavior of using
      a `TypeError` rather than a `ValueError` when there is a problem with its
      `tp` argument.
* Drop support for Python 3.6. **(Breaking change)**
    * Python 3.6 is end-of-life.

### v0.5.0

* `isassignable()` is introduced to the API:
    * `isassignable()` leverages `trycast()` to enable type-checking
      of values against type objects (i.e. type forms) provided at
      runtime, using the same PEP 484 typechecking rules used by
      typecheckers such as mypy.
* Extend `trycast()` to recognize `Required[]` and `NotRequired[]` from
  [PEP 655], as imported from `typing_extensions`.
* Extend `trycast()` to support a `strict` parameter that controls whether it
  accepts `mypy_extensions.TypedDict` or Python 3.8 `typing.TypedDict`
  instances (which lack certain runtime type information necessary for
  accurate runtime typechecking).
    * For now `strict=False` by default for backward compatibility
      with earlier versions of `trycast()`, but this default is expected
      to be altered to `strict=True` when/before trycast v1.0.0 is released.
* Rename primary development branch from `master` to `main`.

[PEP 655]: https://www.python.org/dev/peps/pep-0655/

### v0.4.0

* Upgrade development status from Alpha to Beta:
    * trycast is thoroughly tested.
    * trycast has high code coverage (92% on Python 3.9).
    * trycast has been in production use for over a year
      at [at least one company] without issues.
* Add support for Python 3.10.
* Setup continuous integration with GitHub Actions, against Python 3.6 - 3.10.
* Migrate to the Black code style.
* Introduce Black and isort code formatters.
* Introduce flake8 linter.
* Introduce coverage.py code coverage reports.

[at least one company]: https://dafoster.net/projects/techsmart-platform/

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
    * Recognize TypedDicts that have mixed required and not-required keys correctly.
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

### v0.0.1a

* Initial release.
* Supports typechecking all types found in JSON.
