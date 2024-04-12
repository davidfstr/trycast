# trycast

<img src="https://raw.githubusercontent.com/davidfstr/trycast/main/README/trycast-logo.svg" title="trycast logo" align="right" />

Trycast helps parses JSON-like values whose shape is defined by
[typed dictionaries](https://www.python.org/dev/peps/pep-0589/#abstract)
(TypedDicts) and other standard Python type hints.

You can use the `trycast()`, `checkcast()`, or `isassignable()` functions below
for parsing:


### trycast()

Here is an example of parsing a `Point2D` object defined as a `TypedDict`
using `trycast()`:

```python
from bottle import HTTPResponse, request, route  # Bottle is a web framework
from trycast import trycast
from typing import TypedDict

class Point2D(TypedDict):
    x: float
    y: float
    name: str

@route('/draw_point')
def draw_point_endpoint() -> HTTPResponse:
    request_json = request.json  # type: object
    if (point := trycast(Point2D, request_json)) is None:
        return HTTPResponse(status=400)  # Bad Request
    draw_point(point)  # type is narrowed to Point2D
    return HTTPResponse(status=200)

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
    if (shape := trycast(Shape, request_json)) is None:
        return HTTPResponse(status=400)  # Bad Request
    draw_shape(shape)  # type is narrowed to Shape
    return HTTPResponse(status=200)  # OK
```

> **Important:** Current limitations in the mypy typechecker require that you
> add an extra `cast(Optional[Shape], ...)` around the call to `trycast`
> in the example so that it is accepted by the typechecker without complaining:
> 
> ```python
> shape = cast(Optional[Shape], trycast(Shape, request_json))
> if shape is None:
>     ...
> ```
> 
> These limitations are in the process of being resolved by
> [introducing TypeForm support to mypy](https://github.com/python/mypy/issues/9773).

### checkcast()

`checkcast()` is similar to `trycast()` but instead of returning `None` 
when parsing fails it raises an exception explaining why and where the 
parsing failed.

Here is an example of parsing a `Circle` object using `checkcast()`:

```python
>>> from typing import Literal, TypedDict
>>> from trycast import checkcast
>>> 
>>> class Point2D(TypedDict):
...     x: float
...     y: float
... 
>>> class Circle(TypedDict):
...     type: Literal['circle']
...     center: Point2D  # a nested TypedDict!
...     radius: float
... 
>>> checkcast(Circle, {"type": "circle", "center": {"x": 1}, "radius": 10})
Traceback (most recent call last):
  ...
trycast.ValidationError: Expected Circle but found {'type': 'circle', 'center': {'x': 1}, 'radius': 10}
  At key 'center': Expected Point2D but found {'x': 1}
    Required key 'y' is missing
>>> 
```

`ValidationError` only spends time generating a message if you try to print it
or stringify it, so can be cheaply caught if you only want to use it for
control flow purposes.


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
    if not isassignable(request_json, Shape):
        return HTTPResponse(status=400)  # Bad Request
    draw_shape(request_json)  # type is narrowed to Shape
    return HTTPResponse(status=200)  # OK
```

> **Important:** Current limitations in the mypy typechecker prevent the
> automatic narrowing of the type of `request_json` in the above example to
> `Shape`, so you must add an additional `cast()` to narrow the type manually:
> 
> ```python
> if not isassignable(request_json, Shape):
>     ...
> shape = cast(Shape, request_json)  # type is manually narrowed to Shape
> draw_shape(shape)
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

### Why use trycast?

The trycast module is primarily designed for **recognizing JSON-like structures**
that can be described by Python's typing system. Secondarily, it can be used 
for **recognizing arbitrary structures** that can be described by 
Python's typing system.

Please see [Philosophy] for more information about how trycast
differs from similar libraries like pydantic.

[Philosophy]: https://github.com/davidfstr/trycast/wiki/Philosophy

### Why use TypedDict?

Typed dictionaries are the natural form that JSON data comes in over the wire.
They can be trivially serialized and deserialized without any additional logic.
For applications that use a lot of JSON data - such as web applications - 
using typed dictionaries is very convenient for representing data structures.

If you just need a lightweight class structure that doesn't need excellent
support for JSON-serialization you might consider other alternatives for
representing data structures in Python such as [dataclasses] (**recommended**),
[named tuples], [attrs], or plain classes.

[dataclasses]: https://www.python.org/dev/peps/pep-0557/#abstract
[named tuples]: https://docs.python.org/3/library/typing.html#typing.NamedTuple
[attrs]: https://www.attrs.org/en/stable/


## Installation

```shell
python -m pip install trycast
```


## Recommendations while using trycast

- So that `trycast()` can recognize TypedDicts with mixed required and
  not-required keys correctly:
    * Use Python 3.9+ if possible.
    * Prefer using `typing.TypedDict`, unless you must use Python 3.8.
      In Python 3.8 prefer `typing_extensions.TypedDict` instead.
    * Avoid using `mypy_extensions.TypedDict` in general.


## Presentations & Videos

A presentation about **using trycast to parse JSON** was given at the
2021 PyCon US Typing Summit:

[![2021 PyCon US Typing Summit Presentation](https://raw.githubusercontent.com/davidfstr/trycast/main/README/TypingSummit2021_Presentation_FirstSlide.png)](https://youtu.be/ld9rwCvGdhc?t=1782)

A presentation describing **tools that use Python type annotations at runtime**,
including trycast, was given at the 2022 PyCon US Typing Summit:

[![2022 PyCon US Typing Summit Presentation](https://raw.githubusercontent.com/davidfstr/trycast/main/README/TypingSummit2022_Presentation_FirstSlide.png)](https://youtu.be/CmXQOoiMy-g)

## Contributing

Pull requests are welcome! The [Python Community Code of Conduct] does apply.

[Python Community Code of Conduct]: https://www.python.org/psf/conduct/

You can checkout the code locally using:

```
git clone git@github.com:davidfstr/trycast.git
cd trycast
```

Create your local virtual environment to develop in using [Poetry]:

[Poetry]: https://python-poetry.org/

```
poetry shell
poetry install
```

You can run the existing automated tests in the current version of Python with:

```
make test
```

You can also run the tests against *all* supported Python versions with:

```
make testall
```

See additional development commands by running:

```
make help
```


## License

[MIT](LICENSE.md)


## Feature Reference

### Typing Features Supported

* Scalars
    * bool
    * int
    * float
    * None, type(None)
* Strings
    * str
* Raw Collections
    * list, List
    * tuple, Tuple
    * Sequence, MutableSequence
    * dict, Dict
    * Mapping, MutableMapping
* Generic Collections
  (including [PEP 585](https://peps.python.org/pep-0585/))
    * list[T], List[T]
    * tuple[T, ...], Tuple[T, ...]
    * Sequence[T], MutableSequence[T]
    * dict[K, V], Dict[K, V]
    * Mapping[K, V], MutableMapping[K, V]
* TypedDict
    * typing.TypedDict, typing_extensions.TypedDict
      ([PEP 589](https://peps.python.org/pep-0589/))
    * mypy_extensions.TypedDict (when strict=False)
    * –––
    * Required, NotRequired
      ([PEP 655](https://peps.python.org/pep-0655/))
    * ReadOnly
      ([PEP 705](https://peps.python.org/pep-0705/))
* Tuples (Heterogeneous)
    * tuple[T1], tuple[T1, T2], tuple[T1, T2, T3], etc
    * Tuple[T1], Tuple[T1, T2], Tuple[T1, T2, T3], etc
* Unions
    * Union[X, Y]
    * Optional[T]
    * X | Y
      ([PEP 604](https://peps.python.org/pep-0604/))
* Literals
    * Literal[value]
      ([PEP 586](https://peps.python.org/pep-0586/))
* Callables
    * Callable
    * Callable[P, R] (where P=[Any]\*N and R=Any)
* NewTypes (when strict=False)
* Special Types
    * Any
    * Never
    * NoReturn

### Type Checkers Supported

Trycast does type check successfully with the following type checkers:

* [Mypy]
* [Pyright] / [Pylance]
* [Pyre]
* [Pytype]


## API Reference

<a name="trycast-api"></a>
### trycast API

```
def trycast(
    tp: TypeForm[T]† | TypeFormString[T]‡,
    value: object,
    /, failure: F = None,
    *, strict: bool = True,
    eval: bool = True
) -> T | F: ...
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

Similar to isinstance(), this method considers every bool value to
also be a valid int value, as consistent with Python typecheckers:

> trycast(int, True) -> True  
> isinstance(True, int) -> True

Note that unlike isinstance(), this method considers every int value to
also be a valid float or complex value, as consistent with Python typecheckers:

> trycast(float, 1) -> 1  
> trycast(complex, 1) -> 1  
> isinstance(1, float) -> False  
> isinstance(1, complex) -> False

Note that unlike isinstance(), this method considers every float value to
also be a valid complex value, as consistent with Python typecheckers:

> trycast(complex, 1.0) -> 1  
> isinstance(1.0, complex) -> False

Parameters:

* **strict** -- 
    * If strict=False then this function will additionally accept
      mypy_extensions.TypedDict instances and Python 3.8 typing.TypedDict
      instances for the `tp` parameter. Normally these kinds of types are
      rejected with a TypeNotSupportedError because these
      types do not preserve enough information at runtime to reliably
      determine which keys are required and which are potentially-missing.
    * If strict=False then `NewType("Foo", T)` will be treated
      the same as `T`. Normally NewTypes are rejected with a
      TypeNotSupportedError because values of NewTypes at runtime
      are indistinguishable from their wrapped supertype.
* **eval** --
  If eval=False then this function will not attempt to resolve string
  type references, which requires the use of the eval() function.
  Otherwise string type references will be accepted.

Raises:

* **TypeNotSupportedError** --
    * If strict=True and either mypy_extensions.TypedDict or a
      Python 3.8 typing.TypedDict is found within the `tp` argument.
    * If strict=True and a NewType is found within the `tp` argument.
    * If a TypeVar is found within the `tp` argument.
    * If an unrecognized Generic type is found within the `tp` argument.
* **UnresolvedForwardRefError** --
  If `tp` is a type form which contains a ForwardRef.
* **UnresolvableTypeError** --
  If `tp` is a string that could not be resolved to a type.

Footnotes:

* † TypeForm[T] is a [type annotation object]. For example: `list[str]`

* ‡ TypeFormString[T] is a stringified [type annotation object]. For example: `"list[str]"`

[type annotation object]: https://github.com/python/mypy/issues/9773


### checkcast API

```
def checkcast(
    tp: TypeForm[T]† | TypeFormString[T]‡,
    value: object,
    /, *, strict: bool = True,
    eval: bool = True
) -> T: ...
```

If `value` is in the shape of `tp` (as accepted by a Python typechecker
conforming to PEP 484 "Type Hints") then returns it, otherwise
raises ValidationError.

This method logically performs an operation similar to:

```
if isinstance(tp, value):
    return value
else:
    raise ValidationError(tp, value)
```

except that it supports many more types than `isinstance`, including:

* List[T]
* Dict[K, V]
* Optional[T]
* Union[T1, T2, ...]
* Literal[...]
* T extends TypedDict

See [trycast.trycast]\() for information about parameters,
raised exceptions, and other details.

Raises:

* **ValidationError** -- If `value` is not in the shape of `tp`.
* **TypeNotSupportedError**
* **UnresolvedForwardRefError**
* **UnresolvableTypeError**

[trycast.trycast]: #trycast-api


### isassignable API

```
def isassignable(
    value: object,
    tp: TypeForm[T]† | TypeFormString[T]‡,
    /, *, eval: bool = True
) -> TypeGuard[T]: ...
```

Returns whether `value` is in the shape of `tp`
(as accepted by a Python typechecker conforming to PEP 484 "Type Hints").

This method logically performs an operation similar to:

```
return isinstance(value, tp)
```

except that it supports many more types than `isinstance`, including:

* List[T]
* Dict[K, V]
* Optional[T]
* Union[T1, T2, ...]
* Literal[...]
* T extends TypedDict

See [trycast.trycast]\(..., strict=True) for information about parameters,
raised exceptions, and other details.

[trycast.trycast]: #trycast-api


## Changelog

### Future

* See the [Roadmap](https://github.com/davidfstr/trycast/wiki/Roadmap).

### v1.2.0

* Add `checkcast()`, an alternative to `trycast()` which raises a
  `ValidationError` upon failure instead of returning `None`.
  ([#16](https://github.com/davidfstr/trycast/issues/16))
* Add support for Python 3.13.
    * Recognize `ReadOnly[]` from PEP 705.
      ([#25](https://github.com/davidfstr/trycast/issues/25))
* Add support for Python 3.12.
    * Recognize `type` statements from PEP 695.
      ([#29](https://github.com/davidfstr/trycast/issues/29))
* Enhance support for Python 3.11:
    * Recognize special `Never` values.
      ([#26](https://github.com/davidfstr/trycast/issues/26))
* Drop support for Python 3.7. ([#21](https://github.com/davidfstr/trycast/issues/21))
* Enforce that calls to `trycast()` and `isassignable()` pass the
  first 2 arguments in positional fashion and not in a named fashion:
  ([#18](https://github.com/davidfstr/trycast/issues/18))
  **(Breaking change)**
    * Yes: `trycast(T, value)`, `isassignable(value, T)`
    * No: `trycast(tp=T, value=value)`, `isassignable(value=value, tp=T)`

### v1.1.0

* Fix `trycast()` to recognize TypedDicts with extra keys. ([#19](https://github.com/davidfstr/trycast/issues/19))
    * This new behavior helps recognize JSON structures with arbitrary additional keys
      and is consistent with how static typecheckers treat additional keys.
* Fix magic wand in logo to look more like a magic wand. ([#20](https://github.com/davidfstr/trycast/issues/20))

### v1.0.0

* Extend `trycast()` to recognize more kinds of types:
    * Extend `trycast()` to recognize `set[T]` and `Set[T]` values.
    * Extend `trycast()` to recognize `frozenset[T]` and `FrozenSet[T]` values.
    * Extend `trycast()` to recognize `Callable` and `Callable[P, R]` types when `P` and `R` only contain `Any`.
    * Extend `trycast()` to recognize `NewType` types when strict=False.
    * Extend `trycast()` to explicitly disallow `TypeVar` types.
    * Extend `trycast()` to explicitly disallow unrecognized `Generic` types.
* Fix issues with PEP 484 conformance: **(Breaking change)**
    * `bool` values are now correctly treated as assignable to `int`.
    * `bool`, `int`, and `float` values are now correctly treated as assignable to `complex`.
* Add support for Python 3.11.
* Documentation improvements:
    * Add installation instructions.
    * Improve differentiation from similar libraries.
    * Document supported typing features & type checkers.
    * Mention that trycast() and isassignable() accept TypeFormString[T]
      in addition to TypeForm[T].
    * Add developer documentation.

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
