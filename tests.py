# flake8: noqa
import functools
import os
import platform
import subprocess
import sys
import typing
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from textwrap import dedent
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    FrozenSet,
    Generic,
    Iterator,
    List,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    NewType,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
)
from typing import (
    TypedDict as NativeTypedDict,  # type: ignore[not-supported-yet]  # pytype
)
from typing import TypeVar, Union, cast
from unittest import SkipTest, TestCase

import mypy_extensions

import test_data.forwardrefs_example
import test_data.forwardrefs_example_with_import_annotations
from tests_shape_example import HTTP_400_BAD_REQUEST, draw_shape_endpoint, shapes_drawn
from trycast import (
    TypeNotSupportedError,
    UnresolvableTypeError,
    UnresolvedForwardRefError,
    ValidationError,
)
from trycast import __all__ as trycast_all
from trycast import checkcast, isassignable, trycast

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

# Never
if sys.version_info >= (3, 11):
    from typing import Never

# ReadOnly
try:
    from typing import ReadOnly  # type: ignore[attr-defined]
except ImportError:
    from typing_extensions import ReadOnly  # type: ignore[21]  # pyre

# eval_type
if sys.version_info >= (3, 13):
    from typing import _eval_type  # type: ignore[attr-defined]

    def eval_type(x, y, z):
        return _eval_type(x, y, z, type_params=())

else:
    from typing import _eval_type as eval_type  # type: ignore[attr-defined]

# ParamSpec
if sys.version_info >= (3, 13):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec

_FAILURE = object()


# ------------------------------------------------------------------------------
# API: TestTryCastModule


class TestTryCastModule(TestCase):
    def test_import_star_from_trycast_does_only_import_appropriate_functions(
        self,
    ) -> None:
        self.assertEqual(
            {
                "checkcast",
                "isassignable",
                "trycast",
            },
            set(trycast_all),
        )


# ------------------------------------------------------------------------------
# API: TestTryCast

_T = TypeVar("_T")


# For test_generic_types
class _CellClass(Generic[_T]):
    value: _T

    def __init__(self, value: _T) -> None:
        self.value = value


# For test_uniontype
class _Movie(RichTypedDict):
    name: str
    year: int


class _Movie_NativeTypedDict(NativeTypedDict):
    name: str
    year: int


# For test_typeddict_single_inheritance
class _BookBasedMovie(_Movie):
    based_on: str


# For test_typeddict_single_inheritance_with_mixed_totality
class _MaybeBookBasedMovie(_Movie, total=False):
    based_on: str


# For test_typeddict_single_inheritance_with_mixed_totality
class _MaybeBookBasedMovie_NativeTypedDict(_Movie_NativeTypedDict, total=False):
    based_on: str


class _MaybeMovie(RichTypedDict, total=False):
    name: str
    year: int


class _MaybeMovie_NativeTypedDict(NativeTypedDict, total=False):
    name: str
    year: int


# For test_typeddict_single_inheritance_with_mixed_totality
class _BookBasedMaybeMovie(_MaybeMovie):
    based_on: str


# For test_typeddict_single_inheritance_with_mixed_totality
class _BookBasedMaybeMovie_NativeTypedDict(_MaybeMovie_NativeTypedDict):
    based_on: str


class _X(RichTypedDict):
    x: int


class _Y(RichTypedDict):
    y: str


# For test_typeddict_multiple_inheritance
class _XYZ(_X, _Y):
    z: bool


# For test_callable
# For test_callable_p_r
class _CallableObjectWithZeroArgs:
    def __call__(self) -> None:
        pass


# For test_callable_p_r
class _CallableObjectWithOneArg:
    def __call__(self, value: str) -> None:
        pass


# For test_callable_p_r
class _TypeWithZeroArgConstructor:
    def __init__(self) -> None:
        pass


# For test_callable_p_r
class _TypeWithOneArgConstructor:
    def __init__(self, value: str) -> None:
        pass


_R = TypeVar("_R")


# For test_callable_p_r
def _count_arguments(func: Callable[[int], _R]) -> Callable[..., _R]:
    @functools.wraps(func)
    def inner(*args):
        return func(len(args))

    return inner


# For test_newtype
_Url = NewType("_Url", str)


class TestTryCast(TestCase):
    """
    Tests whether trycast() accepts or rejects various combinations of
    (type × value).

    For testing the details of the ValidationErrors issued by rejections,
    in the higher-level checkcast() API, see the TestCheckCast suite instead.

    Duplicate suite structures are used by TestCheckCast and TestTryCast,
    so it's useful to update both suites at the same time.
    """

    # === Scalars ===

    def test_bool(self) -> None:
        # Actual bools
        self.assertTryCastSuccess(bool, True)
        self.assertTryCastSuccess(bool, False)

        # bool-like ints
        self.assertTryCastFailure(bool, 0)
        self.assertTryCastFailure(bool, 1)

        # bool-like strs
        self.assertTryCastFailure(bool, "True")

        # Falsy values
        self.assertTryCastFailure(bool, 0)
        self.assertTryCastFailure(bool, "")
        self.assertTryCastFailure(bool, [])
        self.assertTryCastFailure(bool, {})
        self.assertTryCastFailure(bool, set())

        # Truthy values
        self.assertTryCastFailure(bool, 1)
        self.assertTryCastFailure(bool, "foo")
        self.assertTryCastFailure(bool, [1])
        self.assertTryCastFailure(bool, {1: 1})
        self.assertTryCastFailure(bool, {1})
        self.assertTryCastFailure(bool, object())

    def test_int(self) -> None:
        # Actual ints
        self.assertTryCastSuccess(int, 0)
        self.assertTryCastSuccess(int, 1)
        self.assertTryCastSuccess(int, 2)
        self.assertTryCastSuccess(int, -1)
        self.assertTryCastSuccess(int, -2)

        # Actual bools
        self.assertTryCastSuccess(int, False)
        self.assertTryCastSuccess(int, True)

        # int-like floats
        self.assertTryCastFailure(int, 0.0)
        self.assertTryCastFailure(int, 1.0)
        self.assertTryCastFailure(int, -1.0)

        # int-like strs
        self.assertTryCastFailure(int, "0")
        self.assertTryCastFailure(int, "1")
        self.assertTryCastFailure(int, "-1")

        # bool-like strs
        self.assertTryCastFailure(int, "True")

        # non-ints
        self.assertTryCastFailure(int, "foo")
        self.assertTryCastFailure(int, [1])
        self.assertTryCastFailure(int, {1: 1})
        self.assertTryCastFailure(int, {1})
        self.assertTryCastFailure(int, object())

    def test_float(self) -> None:
        # Actual floats, parsable by json.loads(...)
        self.assertTryCastSuccess(float, 0.0)
        self.assertTryCastSuccess(float, 0.5)
        self.assertTryCastSuccess(float, 1.0)
        self.assertTryCastSuccess(float, 2e20)
        self.assertTryCastSuccess(float, 2e-20)

        # Actual floats, parsable by json.loads(..., allow_nan=True)
        self.assertTryCastSuccess(float, float("inf"))
        self.assertTryCastSuccess(float, float("-inf"))
        self.assertTryCastSuccess(float, float("nan"))

        # Actual ints
        self.assertTryCastSuccess(float, 0)
        self.assertTryCastSuccess(float, 1)
        self.assertTryCastSuccess(float, 2)
        self.assertTryCastSuccess(float, -1)
        self.assertTryCastSuccess(float, -2)

        # Actual bools
        self.assertTryCastSuccess(float, False)
        self.assertTryCastSuccess(float, True)

        # float-like strs
        self.assertTryCastFailure(float, "1.0")
        self.assertTryCastFailure(float, "inf")
        self.assertTryCastFailure(float, "Infinity")

        # int-like strs
        self.assertTryCastFailure(float, "0")
        self.assertTryCastFailure(float, "1")
        self.assertTryCastFailure(float, "-1")

        # bool-like strs
        self.assertTryCastFailure(float, "True")

        # non-floats
        self.assertTryCastFailure(float, "foo")
        self.assertTryCastFailure(float, [1])
        self.assertTryCastFailure(float, {1: 1})
        self.assertTryCastFailure(float, {1})
        self.assertTryCastFailure(float, object())

    def test_complex(self) -> None:
        # Actual complexs
        self.assertTryCastSuccess(complex, 1j)

        # Actual floats
        self.assertTryCastSuccess(complex, 1.0)

        # Actual ints
        self.assertTryCastSuccess(complex, 1)

        # Actual bools
        self.assertTryCastSuccess(complex, True)

        # complex-like strs
        self.assertTryCastFailure(complex, "1j")

        # float-like strs
        self.assertTryCastFailure(complex, "1.0")

        # int-like strs
        self.assertTryCastFailure(complex, "0")

        # bool-like strs
        self.assertTryCastFailure(complex, "True")

        # non-complexs
        self.assertTryCastFailure(complex, "foo")
        self.assertTryCastFailure(complex, [1])
        self.assertTryCastFailure(complex, {1: 1})
        self.assertTryCastFailure(complex, {1})
        self.assertTryCastFailure(complex, object())

    def test_numerics(self) -> None:
        """
        Verifies that trycast agrees with special typechecker
        rules for {bool, int, float, complex}, as least as far
        as {mypy, pyre, pyright} are concerned as of 2022-05-07.
        """
        self.assertTryCastSuccess(bool, True)
        self.assertTryCastSuccess(int, True)
        self.assertTryCastSuccess(float, True)
        self.assertTryCastSuccess(complex, True)

        self.assertTryCastFailure(bool, 1)
        self.assertTryCastSuccess(int, 1)
        self.assertTryCastSuccess(float, 1)
        self.assertTryCastSuccess(complex, 1)

        self.assertTryCastFailure(bool, 1.0)
        self.assertTryCastFailure(int, 1.0)
        self.assertTryCastSuccess(float, 1.0)
        self.assertTryCastSuccess(complex, 1.0)

        self.assertTryCastFailure(bool, 1j)
        self.assertTryCastFailure(int, 1j)
        self.assertTryCastFailure(float, 1j)
        self.assertTryCastSuccess(complex, 1j)

    def test_none(self) -> None:
        # None object, which is specially treated as type(None)
        self.assertTryCastNoneSuccess(None)

        # Stringified None object, which is specially treated as type(None)
        self.assertTryCastNoneSuccess("None")

    def test_none_type(self) -> None:
        # Actual None
        self.assertTryCastNoneSuccess(type(None))

        # non-None
        self.assertTryCastFailure(type(None), 0)
        self.assertTryCastFailure(type(None), "foo")
        self.assertTryCastFailure(type(None), [1])
        self.assertTryCastFailure(type(None), {1: 1})
        self.assertTryCastFailure(type(None), {1})
        self.assertTryCastFailure(type(None), object())

    # === Strings ===

    def test_str(self) -> None:
        # Actual strs
        self.assertTryCastSuccess(str, "")
        self.assertTryCastSuccess(str, "x")
        self.assertTryCastSuccess(str, "xy")

        # str-like Sequences
        self.assertTryCastFailure(str, b"")
        self.assertTryCastFailure(str, b"x")
        self.assertTryCastFailure(str, b"xy")

        # non-strs
        self.assertTryCastFailure(str, True)
        self.assertTryCastFailure(str, 1)
        self.assertTryCastFailure(str, 1.0)
        self.assertTryCastFailure(str, [1])
        self.assertTryCastFailure(str, {1: 1})
        self.assertTryCastFailure(str, {1})
        self.assertTryCastFailure(str, object())

    # === Raw Collections ===

    def test_list(self) -> None:
        # Actual list
        self.assertTryCastSuccess(list, [])
        self.assertTryCastSuccess(list, [1])
        self.assertTryCastSuccess(list, [1, 2])

        # list-like tuples
        self.assertTryCastFailure(list, ())
        self.assertTryCastFailure(list, (1,))
        self.assertTryCastFailure(list, (1, 2))

        # list-like sets
        self.assertTryCastFailure(list, set())
        self.assertTryCastFailure(list, {1})
        self.assertTryCastFailure(list, {1, 2})

        # non-lists
        self.assertTryCastFailure(list, 0)
        self.assertTryCastFailure(list, "foo")
        self.assertTryCastFailure(list, {1: 1})
        self.assertTryCastFailure(list, {1})
        self.assertTryCastFailure(list, object())

    def test_big_list(self) -> None:
        # Actual list
        self.assertTryCastSuccess(List, [])
        self.assertTryCastSuccess(List, [1])
        self.assertTryCastSuccess(List, [1, 2])

        # list-like tuples
        self.assertTryCastFailure(List, ())
        self.assertTryCastFailure(List, (1,))
        self.assertTryCastFailure(List, (1, 2))

        # list-like sets
        self.assertTryCastFailure(List, set())
        self.assertTryCastFailure(List, {1})
        self.assertTryCastFailure(List, {1, 2})

        # non-lists
        self.assertTryCastFailure(List, 0)
        self.assertTryCastFailure(List, "foo")
        self.assertTryCastFailure(List, {1: 1})
        self.assertTryCastFailure(List, {1})
        self.assertTryCastFailure(List, object())

    def test_set(self) -> None:
        # Actual set
        self.assertTryCastSuccess(set, set())
        self.assertTryCastSuccess(set, {1})
        self.assertTryCastSuccess(set, {1, 2})

        # set-like tuples
        self.assertTryCastFailure(set, ())
        self.assertTryCastFailure(set, (1,))
        self.assertTryCastFailure(set, (1, 2))

        # set-like lists
        self.assertTryCastFailure(set, [])
        self.assertTryCastFailure(
            set,
            [
                1,
            ],
        )
        self.assertTryCastFailure(set, [1, 2])

        # non-sets
        self.assertTryCastFailure(set, 0)
        self.assertTryCastFailure(set, "foo")
        self.assertTryCastFailure(set, {1: 1})
        self.assertTryCastFailure(set, object())

    def test_big_set(self) -> None:
        # Actual set
        self.assertTryCastSuccess(Set, set())
        self.assertTryCastSuccess(Set, {1})
        self.assertTryCastSuccess(Set, {1, 2})

        # set-like tuples
        self.assertTryCastFailure(Set, ())
        self.assertTryCastFailure(Set, (1,))
        self.assertTryCastFailure(Set, (1, 2))

        # set-like lists
        self.assertTryCastFailure(Set, [])
        self.assertTryCastFailure(
            Set,
            [
                1,
            ],
        )
        self.assertTryCastFailure(Set, [1, 2])

        # non-sets
        self.assertTryCastFailure(Set, 0)
        self.assertTryCastFailure(Set, "foo")
        self.assertTryCastFailure(Set, {1: 1})
        self.assertTryCastFailure(Set, object())

    def test_frozenset(self) -> None:
        # Actual frozenset
        self.assertTryCastSuccess(frozenset, frozenset())
        self.assertTryCastSuccess(frozenset, frozenset({1}))
        self.assertTryCastSuccess(frozenset, frozenset({1, 2}))

        # frozenset-like tuples
        self.assertTryCastFailure(frozenset, ())
        self.assertTryCastFailure(frozenset, (1,))
        self.assertTryCastFailure(frozenset, (1, 2))

        # frozenset-like lists
        self.assertTryCastFailure(frozenset, [])
        self.assertTryCastFailure(
            frozenset,
            [
                1,
            ],
        )
        self.assertTryCastFailure(frozenset, [1, 2])

        # frozenset-like sets
        self.assertTryCastFailure(frozenset, {1})

        # non-frozensets
        self.assertTryCastFailure(frozenset, 0)
        self.assertTryCastFailure(frozenset, "foo")
        self.assertTryCastFailure(frozenset, {1: 1})
        self.assertTryCastFailure(frozenset, object())

    def test_big_frozenset(self) -> None:
        # Actual frozenset
        self.assertTryCastSuccess(FrozenSet, frozenset())
        self.assertTryCastSuccess(FrozenSet, frozenset({1}))
        self.assertTryCastSuccess(FrozenSet, frozenset({1, 2}))

        # frozenset-like tuples
        self.assertTryCastFailure(FrozenSet, ())
        self.assertTryCastFailure(FrozenSet, (1,))
        self.assertTryCastFailure(FrozenSet, (1, 2))

        # frozenset-like lists
        self.assertTryCastFailure(FrozenSet, [])
        self.assertTryCastFailure(
            FrozenSet,
            [
                1,
            ],
        )
        self.assertTryCastFailure(FrozenSet, [1, 2])

        # frozenset-like sets
        self.assertTryCastFailure(FrozenSet, {1})

        # non-frozensets
        self.assertTryCastFailure(FrozenSet, 0)
        self.assertTryCastFailure(FrozenSet, "foo")
        self.assertTryCastFailure(FrozenSet, {1: 1})
        self.assertTryCastFailure(FrozenSet, object())

    def test_tuple(self) -> None:
        # Actual tuple
        self.assertTryCastSuccess(tuple, ())
        self.assertTryCastSuccess(tuple, (1,))
        self.assertTryCastSuccess(tuple, (1, 2))

        # tuple-like lists
        self.assertTryCastFailure(tuple, [])
        self.assertTryCastFailure(tuple, [1])
        self.assertTryCastFailure(tuple, [1, 2])

        # tuple-like sets
        self.assertTryCastFailure(tuple, set())
        self.assertTryCastFailure(tuple, {1})
        self.assertTryCastFailure(tuple, {1, 2})

        # non-tuples
        self.assertTryCastFailure(tuple, 0)
        self.assertTryCastFailure(tuple, "foo")
        self.assertTryCastFailure(tuple, {1: 1})
        self.assertTryCastFailure(tuple, {1})
        self.assertTryCastFailure(tuple, object())

    def test_big_tuple(self) -> None:
        # Actual tuple
        self.assertTryCastSuccess(Tuple, ())
        self.assertTryCastSuccess(Tuple, (1,))
        self.assertTryCastSuccess(Tuple, (1, 2))

        # tuple-like lists
        self.assertTryCastFailure(Tuple, [])
        self.assertTryCastFailure(Tuple, [1])
        self.assertTryCastFailure(Tuple, [1, 2])

        # tuple-like sets
        self.assertTryCastFailure(Tuple, set())
        self.assertTryCastFailure(Tuple, {1})
        self.assertTryCastFailure(Tuple, {1, 2})

        # non-tuples
        self.assertTryCastFailure(Tuple, 0)
        self.assertTryCastFailure(Tuple, "foo")
        self.assertTryCastFailure(Tuple, {1: 1})
        self.assertTryCastFailure(Tuple, {1})
        self.assertTryCastFailure(Tuple, object())

    def test_sequence(self) -> None:
        # Actual Sequence
        self.assertTryCastSuccess(Sequence, [])
        self.assertTryCastSuccess(Sequence, [1])
        self.assertTryCastSuccess(Sequence, [1, 2])
        self.assertTryCastSuccess(Sequence, ())
        self.assertTryCastSuccess(Sequence, (1,))
        self.assertTryCastSuccess(Sequence, (1, 2))
        self.assertTryCastSuccess(Sequence, "foo")

        # Sequence-like sets
        self.assertTryCastFailure(Sequence, set())
        self.assertTryCastFailure(Sequence, {1})
        self.assertTryCastFailure(Sequence, {1, 2})

        # non-Sequences
        self.assertTryCastFailure(Sequence, 0)
        self.assertTryCastFailure(Sequence, {1: 1})
        self.assertTryCastFailure(Sequence, {1})
        self.assertTryCastFailure(Sequence, object())

        # Actual MutableSequence
        self.assertTryCastSuccess(MutableSequence, [])
        self.assertTryCastSuccess(MutableSequence, [1])
        self.assertTryCastSuccess(MutableSequence, [1, 2])

        # MutableSequence-like sets
        self.assertTryCastFailure(MutableSequence, set())
        self.assertTryCastFailure(MutableSequence, {1})
        self.assertTryCastFailure(MutableSequence, {1, 2})

        # non-MutableSequences
        self.assertTryCastFailure(MutableSequence, 0)
        self.assertTryCastFailure(MutableSequence, "foo")
        self.assertTryCastFailure(MutableSequence, {1: 1})
        self.assertTryCastFailure(MutableSequence, {1})
        self.assertTryCastFailure(MutableSequence, object())

    def test_dict(self) -> None:
        # Actual dict
        self.assertTryCastSuccess(dict, {})
        self.assertTryCastSuccess(dict, {1: 1})
        self.assertTryCastSuccess(dict, {"x": 1, "y": 1})

        # non-dicts
        self.assertTryCastFailure(dict, 0)
        self.assertTryCastFailure(dict, "foo")
        self.assertTryCastFailure(dict, [1])
        self.assertTryCastFailure(dict, {1})
        self.assertTryCastFailure(dict, object())

    def test_big_dict(self) -> None:
        # Actual dict
        self.assertTryCastSuccess(Dict, {})
        self.assertTryCastSuccess(Dict, {1: 1})
        self.assertTryCastSuccess(Dict, {"x": 1, "y": 1})

        # non-dicts
        self.assertTryCastFailure(Dict, 0)
        self.assertTryCastFailure(Dict, "foo")
        self.assertTryCastFailure(Dict, [1])
        self.assertTryCastFailure(Dict, {1})
        self.assertTryCastFailure(Dict, object())

    def test_mapping(self) -> None:
        # Actual Mapping
        self.assertTryCastSuccess(Mapping, {})
        self.assertTryCastSuccess(Mapping, {1: 1})
        self.assertTryCastSuccess(Mapping, {"x": 1, "y": 1})

        # non-Mapping
        self.assertTryCastFailure(Mapping, 0)
        self.assertTryCastFailure(Mapping, "foo")
        self.assertTryCastFailure(Mapping, [1])
        self.assertTryCastFailure(Mapping, {1})
        self.assertTryCastFailure(Mapping, object())

        # Actual MutableMapping
        self.assertTryCastSuccess(MutableMapping, {})
        self.assertTryCastSuccess(MutableMapping, {1: 1})
        self.assertTryCastSuccess(MutableMapping, {"x": 1, "y": 1})

        # non-MutableMapping
        self.assertTryCastFailure(MutableMapping, 0)
        self.assertTryCastFailure(MutableMapping, "foo")
        self.assertTryCastFailure(MutableMapping, [1])
        self.assertTryCastFailure(MutableMapping, {1})
        self.assertTryCastFailure(MutableMapping, object())

    # === Generic Collections ===

    if sys.version_info >= (3, 9):

        def test_list_t(self) -> None:
            # Actual list[T]
            self.assertTryCastSuccess(list[int], [])
            self.assertTryCastSuccess(list[int], [1])
            self.assertTryCastSuccess(list[int], [1, 2])

            # non-list[T]s
            self.assertTryCastFailure(list[int], 0)
            self.assertTryCastFailure(list[int], "foo")
            self.assertTryCastFailure(list[int], ["1"])
            self.assertTryCastFailure(list[int], {1: 1})
            self.assertTryCastFailure(list[int], {1})
            self.assertTryCastFailure(list[int], object())

    def test_big_list_t(self) -> None:
        # Actual list[T]
        self.assertTryCastSuccess(List[int], [])
        self.assertTryCastSuccess(List[int], [1])
        self.assertTryCastSuccess(List[int], [1, 2])

        # non-list[T]s
        self.assertTryCastFailure(List[int], 0)
        self.assertTryCastFailure(List[int], "foo")
        self.assertTryCastFailure(List[int], ["1"])
        self.assertTryCastFailure(List[int], {1: 1})
        self.assertTryCastFailure(List[int], {1})
        self.assertTryCastFailure(List[int], object())

    if sys.version_info >= (3, 9):

        def test_set_t(self) -> None:
            # Actual set[T]
            self.assertTryCastSuccess(set[int], set())
            self.assertTryCastSuccess(set[int], {1})
            self.assertTryCastSuccess(set[int], {1, 2})

            # non-set[T]s
            self.assertTryCastFailure(set[int], 0)
            self.assertTryCastFailure(set[int], "foo")
            self.assertTryCastFailure(set[int], ["1"])
            self.assertTryCastFailure(set[int], {1: 1})
            self.assertTryCastFailure(set[int], [1])
            self.assertTryCastFailure(set[int], object())

    def test_big_set_t(self) -> None:
        # Actual set[T]
        self.assertTryCastSuccess(Set[int], set())
        self.assertTryCastSuccess(Set[int], {1})
        self.assertTryCastSuccess(Set[int], {1, 2})

        # non-set[T]s
        self.assertTryCastFailure(Set[int], 0)
        self.assertTryCastFailure(Set[int], "foo")
        self.assertTryCastFailure(Set[int], ["1"])
        self.assertTryCastFailure(Set[int], {1: 1})
        self.assertTryCastFailure(Set[int], [1])
        self.assertTryCastFailure(Set[int], object())

    if sys.version_info >= (3, 9):

        def test_frozenset_t(self) -> None:
            # Actual frozenset[T]
            self.assertTryCastSuccess(frozenset[int], frozenset())
            self.assertTryCastSuccess(frozenset[int], frozenset({1}))
            self.assertTryCastSuccess(frozenset[int], frozenset({1, 2}))

            # frozenset-like sets
            self.assertTryCastFailure(frozenset[int], {1})

            # non-frozenset[T]s
            self.assertTryCastFailure(frozenset[int], 0)
            self.assertTryCastFailure(frozenset[int], "foo")
            self.assertTryCastFailure(frozenset[int], ["1"])
            self.assertTryCastFailure(frozenset[int], {1: 1})
            self.assertTryCastFailure(frozenset[int], [1])
            self.assertTryCastFailure(frozenset[int], object())

    def test_big_frozenset_t(self) -> None:
        # Actual frozenset[T]
        self.assertTryCastSuccess(FrozenSet[int], frozenset())
        self.assertTryCastSuccess(FrozenSet[int], frozenset({1}))
        self.assertTryCastSuccess(FrozenSet[int], frozenset({1, 2}))

        # frozenset-like sets
        self.assertTryCastFailure(FrozenSet[int], {1})

        # non-frozenset[T]s
        self.assertTryCastFailure(FrozenSet[int], 0)
        self.assertTryCastFailure(FrozenSet[int], "foo")
        self.assertTryCastFailure(FrozenSet[int], ["1"])
        self.assertTryCastFailure(FrozenSet[int], {1: 1})
        self.assertTryCastFailure(FrozenSet[int], [1])
        self.assertTryCastFailure(FrozenSet[int], object())

    if sys.version_info >= (3, 9):

        def test_tuple_t_ellipsis(self) -> None:
            # Actual tuple[T, ...]
            self.assertTryCastSuccess(tuple[int, ...], ())  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(tuple[int, ...], (1,))  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(tuple[int, ...], (1, 2))  # type: ignore[6]  # pyre

            # non-tuple[T, ...]s
            self.assertTryCastFailure(tuple[int, ...], 0)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, ...], "foo")  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, ...], ["1"])  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, ...], {1: 1})  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, ...], {1})  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, ...], object())  # type: ignore[6]  # pyre

    def test_big_tuple_t_ellipsis(self) -> None:
        # Actual tuple[T, ...]
        self.assertTryCastSuccess(Tuple[int, ...], ())
        self.assertTryCastSuccess(Tuple[int, ...], (1,))
        self.assertTryCastSuccess(Tuple[int, ...], (1, 2))

        # non-tuple[T, ...]s
        self.assertTryCastFailure(Tuple[int, ...], 0)
        self.assertTryCastFailure(Tuple[int, ...], "foo")
        self.assertTryCastFailure(Tuple[int, ...], ["1"])
        self.assertTryCastFailure(Tuple[int, ...], {1: 1})
        self.assertTryCastFailure(Tuple[int, ...], {1})
        self.assertTryCastFailure(Tuple[int, ...], object())

    def test_sequence_t(self) -> None:
        # Actual Sequence[T]
        self.assertTryCastSuccess(Sequence[int], [])
        self.assertTryCastSuccess(Sequence[int], [1])
        self.assertTryCastSuccess(Sequence[int], [1, 2])
        self.assertTryCastSuccess(Sequence[str], "foo")

        # non-Sequence[T]s
        self.assertTryCastFailure(Sequence[int], 0)
        self.assertTryCastFailure(Sequence[int], "foo")
        self.assertTryCastFailure(Sequence[int], ["1"])
        self.assertTryCastFailure(Sequence[int], {1: 1})
        self.assertTryCastFailure(Sequence[int], {1})
        self.assertTryCastFailure(Sequence[int], object())

        # Actual MutableSequence[T]
        self.assertTryCastSuccess(MutableSequence[int], [])
        self.assertTryCastSuccess(MutableSequence[int], [1])
        self.assertTryCastSuccess(MutableSequence[int], [1, 2])

        # non-MutableSequence[T]s
        self.assertTryCastFailure(MutableSequence[int], 0)
        self.assertTryCastFailure(MutableSequence[int], "foo")
        self.assertTryCastFailure(MutableSequence[int], ["1"])
        self.assertTryCastFailure(MutableSequence[int], {1: 1})
        self.assertTryCastFailure(MutableSequence[int], {1})
        self.assertTryCastFailure(MutableSequence[int], object())
        self.assertTryCastFailure(MutableSequence[str], "foo")

    if sys.version_info >= (3, 9):

        def test_dict_k_v(self) -> None:
            # Actual dict[K, V]
            self.assertTryCastSuccess(dict[str, int], {})
            self.assertTryCastSuccess(dict[str, int], {"x": 1})
            self.assertTryCastSuccess(dict[str, int], {"x": 1, "y": 2})

            # non-dict[K, V]s
            self.assertTryCastFailure(dict[str, int], 0)
            self.assertTryCastFailure(dict[str, int], "foo")
            self.assertTryCastFailure(dict[str, int], [1])
            self.assertTryCastFailure(dict[str, int], {1: 1})
            self.assertTryCastFailure(dict[str, int], {1})
            self.assertTryCastFailure(dict[str, int], object())

    def test_big_dict_k_v(self) -> None:
        # Actual dict[K, V]
        self.assertTryCastSuccess(Dict[str, int], {})
        self.assertTryCastSuccess(Dict[str, int], {"x": 1})
        self.assertTryCastSuccess(Dict[str, int], {"x": 1, "y": 2})

        # non-dict[K, V]s
        self.assertTryCastFailure(Dict[str, int], 0)
        self.assertTryCastFailure(Dict[str, int], "foo")
        self.assertTryCastFailure(Dict[str, int], [1])
        self.assertTryCastFailure(Dict[str, int], {1: 1})
        self.assertTryCastFailure(Dict[str, int], {1})
        self.assertTryCastFailure(Dict[str, int], object())

    def test_mapping_k_v(self) -> None:
        # Actual Mapping[K, V]
        self.assertTryCastSuccess(Mapping[str, int], {})
        self.assertTryCastSuccess(Mapping[str, int], {"x": 1})
        self.assertTryCastSuccess(Mapping[str, int], {"x": 1, "y": 2})

        # non-Mapping[K, V]s
        self.assertTryCastFailure(Mapping[str, int], 0)
        self.assertTryCastFailure(Mapping[str, int], "foo")
        self.assertTryCastFailure(Mapping[str, int], [1])
        self.assertTryCastFailure(Mapping[str, int], {1: 1})
        self.assertTryCastFailure(Mapping[str, int], {1})
        self.assertTryCastFailure(Mapping[str, int], object())

        # Actual MutableMapping[K, V]
        self.assertTryCastSuccess(MutableMapping[str, int], {})
        self.assertTryCastSuccess(MutableMapping[str, int], {"x": 1})
        self.assertTryCastSuccess(MutableMapping[str, int], {"x": 1, "y": 2})

        # non-MutableMapping[K, V]s
        self.assertTryCastFailure(MutableMapping[str, int], 0)
        self.assertTryCastFailure(MutableMapping[str, int], "foo")
        self.assertTryCastFailure(MutableMapping[str, int], [1])
        self.assertTryCastFailure(MutableMapping[str, int], {1: 1})
        self.assertTryCastFailure(MutableMapping[str, int], {1})
        self.assertTryCastFailure(MutableMapping[str, int], object())

    # === User-Defined Generic Types ===

    def test_generic_types(self) -> None:
        cell = _CellClass[int](1)
        self.assertTryCastSuccess(_CellClass, cell)
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast does not know how to recognize generic type",
            lambda: trycast(_CellClass[int], cell),
        )

    # === TypedDicts ===

    def test_typeddict(self) -> None:
        class Point2D(RichTypedDict):
            x: int
            y: int

        class PartialPoint2D(RichTypedDict, total=False):
            x: int
            y: int

        class Point3D(RichTypedDict):
            x: int
            y: int
            z: int

        # Point2D
        self.assertTryCastFailure(Point2D, {"x": 1})
        self.assertTryCastSuccess(Point2D, {"x": 1, "y": 1})
        self.assertTryCastFailure(Point2D, {"x": 1, "y": "string"})
        self.assertTryCastSuccess(Point2D, {"x": 1, "y": 1, "z": 1})
        self.assertTryCastSuccess(Point2D, {"x": 1, "y": 1, "z": "string"})

        # PartialPoint2D
        self.assertTryCastSuccess(PartialPoint2D, {"x": 1, "y": 1})
        self.assertTryCastFailure(PartialPoint2D, {"x": 1, "y": "string"})
        self.assertTryCastSuccess(PartialPoint2D, {"y": 1})
        self.assertTryCastSuccess(PartialPoint2D, {"x": 1})
        self.assertTryCastSuccess(PartialPoint2D, {})
        self.assertTryCastSuccess(PartialPoint2D, {"x": 1, "y": 1, "z": 1})
        self.assertTryCastSuccess(PartialPoint2D, {"x": 1, "y": 1, "z": "string"})

        # Point3D
        self.assertTryCastFailure(Point3D, {"x": 1, "y": 1})
        self.assertTryCastSuccess(Point3D, {"x": 1, "y": 1, "z": 1})

    def test_typeddict_with_extra_keys(self) -> None:
        class Packet(RichTypedDict):
            type: str
            payload: str

        class PacketWithExtra(Packet):
            extra: str

        p = PacketWithExtra(type="hello", payload="v1", extra="english")  # type: ignore[28]  # pyre
        p2: Packet = p

        self.assertTryCastSuccess(PacketWithExtra, p)
        self.assertTryCastSuccess(Packet, p2)

    def test_typeddict_single_inheritance(self) -> None:
        _1 = _BookBasedMovie(
            name="Blade Runner",
            year=1982,
            based_on="Blade Runner",
        )
        self.assertTryCastSuccess(
            _BookBasedMovie,
            dict(
                name="Blade Runner",
                year=1982,
                based_on="Blade Runner",
            ),
        )

        self.assertTryCastFailure(
            _BookBasedMovie,
            dict(
                name="Blade Runner",
                year=1982,
            ),
        )
        self.assertTryCastFailure(
            _BookBasedMovie,
            dict(
                based_on="Blade Runner",
            ),
        )

    def test_typeddict_single_inheritance_with_mixed_totality(self) -> None:
        _1 = _MaybeBookBasedMovie(
            name="Blade Runner",
            year=1982,
            based_on="Blade Runner",
        )
        self.assertTryCastSuccess(
            _MaybeBookBasedMovie,
            dict(
                name="Blade Runner",
                year=1982,
                based_on="Blade Runner",
            ),
        )

        _2 = _MaybeBookBasedMovie(
            name="Blade Runner",
            year=1982,
        )
        self.assertTryCastSuccess(
            _MaybeBookBasedMovie,
            dict(
                name="Blade Runner",
                year=1982,
            ),
        )

        self.assertTryCastFailure(
            _MaybeBookBasedMovie,
            dict(
                based_on="Blade Runner",
            ),
            strict=True,
        )
        if sys.version_info >= (3, 8) and sys.version_info < (3, 9):
            # Unfortunately there isn't enough type annotation information
            # preserved at runtime for Python 3.8's typing.TypedDict
            # (or for mypy_extensions.TypedDict in general) to correctly
            # detect that this cast should actually be a failure.
            #
            # To avoid such a problem, users should prefer
            # typing_extensions.TypedDict over typing.TypedDict
            # if they must use Python 3.8 (and cannot upgrade to Python 3.9+).
            self.assertTryCastSuccess(
                _MaybeBookBasedMovie_NativeTypedDict,
                dict(
                    based_on="Blade Runner",
                ),
                strict=False,
            )
        else:
            self.assertTryCastFailure(
                _MaybeBookBasedMovie_NativeTypedDict,
                dict(
                    based_on="Blade Runner",
                ),
                strict=False,
            )

        _3 = _BookBasedMaybeMovie(
            name="Blade Runner",
            year=1982,
            based_on="Blade Runner",
        )
        self.assertTryCastSuccess(
            _BookBasedMaybeMovie,
            dict(
                name="Blade Runner",
                year=1982,
                based_on="Blade Runner",
            ),
        )

        self.assertTryCastFailure(
            _BookBasedMaybeMovie,
            dict(
                name="Blade Runner",
                year=1982,
            ),
        )

        self.assertTryCastSuccess(
            _BookBasedMaybeMovie,
            dict(
                based_on="Blade Runner",
            ),
            strict=True,
        )
        if sys.version_info >= (3, 8) and sys.version_info < (3, 9):
            # Unfortunately there isn't enough type annotation information
            # preserved at runtime for Python 3.8's typing.TypedDict
            # (or for mypy_extensions.TypedDict in general) to correctly
            # detect that this cast should actually be a success.
            #
            # To avoid such a problem, users should prefer
            # typing_extensions.TypedDict over typing.TypedDict
            # if they must use Python 3.8 (and cannot upgrade to Python 3.9+).
            self.assertTryCastFailure(
                _BookBasedMaybeMovie_NativeTypedDict,
                dict(
                    based_on="Blade Runner",
                ),
                strict=False,
            )
        else:
            _4 = _BookBasedMaybeMovie_NativeTypedDict(
                based_on="Blade Runner",
            )
            self.assertTryCastSuccess(
                _BookBasedMaybeMovie_NativeTypedDict,
                dict(
                    based_on="Blade Runner",
                ),
                strict=False,
            )

    def test_typeddict_multiple_inheritance(self) -> None:
        _1 = _XYZ(
            x=1,
            y="2",
            z=True,
        )
        self.assertTryCastSuccess(
            _XYZ,
            dict(
                x=1,
                y="2",
                z=True,
            ),
        )

        self.assertTryCastFailure(
            _XYZ,
            dict(
                y="2",
                z=True,
            ),
        )
        self.assertTryCastFailure(
            _XYZ,
            dict(
                x=1,
                z=True,
            ),
        )
        self.assertTryCastFailure(
            _XYZ,
            dict(
                x=1,
                y="2",
            ),
        )

    def test_typeddict_required_notrequired(self) -> None:
        import typing_extensions

        if sys.version_info >= (3, 11):
            self.assertIs(typing.Required, typing_extensions.Required)  # type: ignore[16]  # pyre
            self.assertIs(typing.NotRequired, typing_extensions.NotRequired)  # type: ignore[16]  # pyre

        class TotalMovie(typing_extensions.TypedDict):  # type: ignore[not-supported-yet]  # pytype
            title: str
            year: typing_extensions.NotRequired[int]  # type: ignore[not-supported-yet]  # pytype

        class NontotalMovie(typing_extensions.TypedDict, total=False):
            title: typing_extensions.Required[str]  # type: ignore[not-supported-yet]  # pytype
            year: int

        # TotalMovie
        self.assertTryCastSuccess(TotalMovie, {"title": "Blade Runner", "year": 1982})
        self.assertTryCastSuccess(TotalMovie, {"title": "Blade Runner"})
        self.assertTryCastFailure(
            TotalMovie, {"title": "Blade Runner", "year": "Blade Runner"}
        )
        self.assertTryCastFailure(TotalMovie, {"year": 1982})

        # NontotalMovie
        self.assertTryCastSuccess(
            NontotalMovie, {"title": "Blade Runner", "year": 1982}
        )
        self.assertTryCastSuccess(NontotalMovie, {"title": "Blade Runner"})
        self.assertTryCastFailure(NontotalMovie, {"title": 1982, "year": 1982})
        self.assertTryCastFailure(NontotalMovie, {"year": 1982})

    def test_typeddict_readonly(self) -> None:
        import typing_extensions

        if sys.version_info >= (3, 13):
            self.assertIs(typing.ReadOnly, typing_extensions.ReadOnly)  # type: ignore[attr-defined, 16]  # mypy, pyre

        class Movie(typing_extensions.TypedDict):  # type: ignore[not-supported-yet]  # pytype
            title: str
            year: int

        class ReadOnlyMovie(typing_extensions.TypedDict):
            title: ReadOnly[str]
            year: ReadOnly[int]

        # Movie
        self.assertTryCastSuccess(Movie, {"title": "Blade Runner", "year": 1982})

        # ReadOnlyMovie
        self.assertTryCastSuccess(
            ReadOnlyMovie, {"title": "Blade Runner", "year": 1982}
        )

    def test_typeddict_using_mapping_value(self) -> None:
        class NamedObject(RichTypedDict):
            name: str

        class ValuedObject(RichTypedDict):
            value: object

        class MyNamedMapping(Mapping):
            def __init__(self, name: str) -> None:
                self._name = name

            def __getitem__(self, key: str) -> object:
                if key == "name":
                    return self._name
                else:
                    raise KeyError  # pragma: no cover

            def __len__(self) -> int:
                return 1  # pragma: no cover

            def __iter__(self):
                return (x for x in ["name"])

        self.assertTryCastSuccess(NamedObject, MyNamedMapping("Isabelle"))
        self.assertTryCastFailure(ValuedObject, MyNamedMapping("Isabelle"))

    # === Tuples (Heterogeneous) ===

    if sys.version_info >= (3, 9):

        def test_tuple_ts(self) -> None:
            # tuple[Ts]
            self.assertTryCastSuccess(tuple[int], (1,))  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(tuple[int, str], (1, "a"))  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(tuple[int, str, bool], (1, "a", True))  # type: ignore[6]  # pyre

            # tuple[Ts]-like tuples
            self.assertTryCastFailure(tuple[int], ("A",))
            self.assertTryCastFailure(tuple[int, str], (1, 2))  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, str, bool], (1, "a", object()))  # type: ignore[6]  # pyre

            # tuple[Ts]-like lists
            self.assertTryCastFailure(tuple[int], [1])
            self.assertTryCastFailure(tuple[int, str], [1, "a"])  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, str, bool], [1, "a", True])  # type: ignore[6]  # pyre

            # non-tuple[Ts]
            self.assertTryCastFailure(tuple[int], 0)
            self.assertTryCastFailure(tuple[int], "foo")
            self.assertTryCastFailure(tuple[int], ["1"])
            self.assertTryCastFailure(tuple[int], {1: 1})
            self.assertTryCastFailure(tuple[int], {1})
            self.assertTryCastFailure(tuple[int], object())

    def test_big_tuple_ts(self) -> None:
        # Tuple[Ts]
        self.assertTryCastSuccess(Tuple[int], (1,))
        self.assertTryCastSuccess(Tuple[int, str], (1, "a"))
        self.assertTryCastSuccess(Tuple[int, str, bool], (1, "a", True))

        # Tuple[Ts]-like tuples
        self.assertTryCastFailure(Tuple[int], ("A",))
        self.assertTryCastFailure(Tuple[int, str], (1, 2))
        self.assertTryCastFailure(Tuple[int, str, bool], (1, "a", object()))

        # Tuple[Ts]-like lists
        self.assertTryCastFailure(Tuple[int], [1])
        self.assertTryCastFailure(Tuple[int, str], [1, "a"])
        self.assertTryCastFailure(Tuple[int, str, bool], [1, "a", True])

        # non-Tuple[Ts]
        self.assertTryCastFailure(Tuple[int], 0)
        self.assertTryCastFailure(Tuple[int], "foo")
        self.assertTryCastFailure(Tuple[int], ["1"])
        self.assertTryCastFailure(Tuple[int], {1: 1})
        self.assertTryCastFailure(Tuple[int], {1})
        self.assertTryCastFailure(Tuple[int], object())

    # === Unions ===

    def test_union(self) -> None:
        # Union[int, str]
        self.assertTryCastSuccess(Union[int, str], 1)
        self.assertTryCastSuccess(Union[int, str], "foo")

        # non-Union[int, str]
        self.assertTryCastFailure(Union[int, str], [])

    def test_optional(self) -> None:
        # Optional[str]
        self.assertTryCastNoneSuccess(Optional[str])
        self.assertTryCastSuccess(Optional[str], "foo")

        # non-Optional[str]
        self.assertTryCastFailure(Optional[str], [])

    if sys.version_info >= (3, 10):

        def test_uniontype(self) -> None:
            # int | str, equivalent to Union[int, str]
            self.assertTryCastSuccess(int | str, 1)  # type: ignore[operator]
            self.assertTryCastSuccess(int | str, "foo")  # type: ignore[operator]

            # non-(int | str)
            self.assertTryCastFailure(int | str, [])  # type: ignore[operator]

            # UnionType with TypedDict
            self.assertTryCastSuccess(_Movie | None, _Movie(name="Blade Runner", year=1982))  # type: ignore[operator]
            self.assertTryCastSuccess(_Movie | None, None)  # type: ignore[operator]
            self.assertTryCastFailure(_Movie | None, {})  # type: ignore[operator]

    # === Literals ===

    def test_literal(self) -> None:
        # Literal
        self.assertTryCastSuccess(Literal["circle"], "circle")
        self.assertTryCastSuccess(Literal[1], 1)
        self.assertTryCastSuccess(Literal[True], True)

        # Literal-like with the wrong value
        self.assertTryCastFailure(Literal["circle"], "square")
        self.assertTryCastFailure(Literal[1], 2)
        self.assertTryCastFailure(Literal[True], False)

        # non-Literal
        self.assertTryCastFailure(Literal["circle"], 0)
        self.assertTryCastFailure(Literal["circle"], "foo")
        self.assertTryCastFailure(Literal["circle"], [1])
        self.assertTryCastFailure(Literal["circle"], {1: 1})
        self.assertTryCastFailure(Literal["circle"], {1})
        self.assertTryCastFailure(Literal["circle"], object())

    # === Callables ===

    def test_callable(self) -> None:
        # Callable
        self.assertTryCastSuccess(Callable, lambda: None)
        self.assertTryCastSuccess(Callable, self.test_callable)
        self.assertTryCastSuccess(Callable, _CallableObjectWithZeroArgs())
        self.assertTryCastSuccess(Callable, str)
        self.assertTryCastFailure(Callable, object())

    def test_callable_p_r(self) -> None:
        # Callable[[], T]
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have a declared return type",
            lambda: trycast(Callable[[], None], lambda: None),  # type: ignore[6]  # pyre
        )
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have a declared return type",
            lambda: trycast(Callable[[], None], self._expects_zero_args),  # type: ignore[6]  # pyre
        )
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have a declared return type",
            lambda: trycast(Callable[[], None], _CallableObjectWithZeroArgs()),  # type: ignore[6]  # pyre
        )
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have a declared return type",
            lambda: trycast(Callable[[], None], _TypeWithZeroArgConstructor),  # type: ignore[6]  # pyre
        )

        # Callable[[], Any]
        if True:
            self.assertTryCastSuccess(Callable[[], Any], lambda: None)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], self._expects_zero_args)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], self._expects_variable_args)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], _CallableObjectWithZeroArgs())  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], _TypeWithZeroArgConstructor)  # type: ignore[6]  # pyre

            self.assertTryCastFailure(Callable[[], Any], lambda x: None)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[], Any], self._expects_one_arg)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[], Any], _CallableObjectWithOneArg())  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[], Any], _TypeWithOneArgConstructor)  # type: ignore[6]  # pyre

            # NOTE: Cannot introspect constructor for certain built-in types lacking __signature__.
            #       See: https://github.com/davidfstr/trycast/issues/15
            if sys.version_info >= (3, 13):
                self.assertTryCastSuccess(Callable[[], Any], bool)  # type: ignore[6]  # pyre
            else:
                self.assertTryCastFailure(Callable[[], Any], bool)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[], Any], int)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], float)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], complex)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[], Any], str)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], list)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[], Any], dict)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[], Any], tuple)  # type: ignore[6]  # pyre

        # Callable[[Any], Any]
        if True:
            self.assertTryCastSuccess(Callable[[Any], Any], lambda x: None)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], self._expects_one_arg)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], self._expects_variable_args)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], _CallableObjectWithOneArg())  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], _TypeWithOneArgConstructor)  # type: ignore[6]  # pyre

            self.assertTryCastFailure(Callable[[Any], Any], lambda: None)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[Any], Any], self._expects_zero_args)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(
                Callable[[Any], Any], _CallableObjectWithZeroArgs()  # type: ignore[6]  # pyre
            )
            self.assertTryCastFailure(Callable[[Any], Any], _TypeWithZeroArgConstructor)  # type: ignore[6]  # pyre

            # NOTE: Cannot introspect constructor for certain built-in types lacking __signature__.
            #       See: https://github.com/davidfstr/trycast/issues/15
            if sys.version_info >= (3, 13):
                self.assertTryCastSuccess(Callable[[Any], Any], bool)  # type: ignore[6]  # pyre
            else:
                self.assertTryCastFailure(Callable[[Any], Any], bool)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[Any], Any], int)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], float)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], complex)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[Any], Any], str)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], list)  # type: ignore[6]  # pyre
            self.assertTryCastFailure(Callable[[Any], Any], dict)  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(Callable[[Any], Any], tuple)  # type: ignore[6]  # pyre

        # Callable[[T], Any]
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have declared parameter types",
            lambda: trycast(Callable[[str], Any], lambda x: None),  # type: ignore[6]  # pyre
        )
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have declared parameter types",
            lambda: trycast(Callable[[str], Any], self._expects_one_arg),  # type: ignore[6]  # pyre
        )
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have declared parameter types",
            lambda: trycast(Callable[[str], Any], _CallableObjectWithOneArg()),  # type: ignore[6]  # pyre
        )
        self.assertRaisesRegex(
            TypeNotSupportedError,
            r"trycast cannot reliably determine whether value is a typing\.Callable.*"
            r"callables at runtime do not always have declared parameter types",
            lambda: trycast(Callable[[str], Any], _TypeWithOneArgConstructor),  # type: ignore[6]  # pyre
        )

        # Ensure looks at unwrapped version of decorated function
        self.assertTryCastSuccess(Callable[[], Any], self._expects_int_arg)  # type: ignore[6]  # pyre
        self.assertTryCastSuccess(Callable[[Any], Any], self._expects_int_arg)  # type: ignore[6]  # pyre
        self.assertTryCastSuccess(Callable[[Any, Any], Any], self._expects_int_arg)  # type: ignore[6]  # pyre

    @staticmethod
    def _expects_zero_args() -> None:
        pass

    @staticmethod
    def _expects_one_arg(value: str) -> None:
        pass

    @staticmethod
    def _expects_variable_args(*args: str) -> None:
        pass

    @_count_arguments  # type: ignore[56]  # pyre
    @staticmethod
    def _expects_int_arg(value: int) -> None:
        pass

    # === NewTypes ===

    def test_newtype(self) -> None:
        # strict=True
        self.assertRaisesRegex(
            TypeNotSupportedError,
            "trycast cannot reliably determine whether value is a NewType",
            lambda: trycast(_Url, _Url("http://example.com")),
        )
        self.assertRaisesRegex(
            TypeNotSupportedError,
            "trycast cannot reliably determine whether value is a NewType",
            lambda: trycast(_Url, "http://example.com"),
        )

        # strict=False
        self.assertTryCastSuccess(_Url, _Url("http://example.com"), strict=False)
        # NOTE: This cast would be *failed* by a typechecker
        self.assertTryCastSuccess(_Url, "http://example.com", strict=False)

        self.assertTryCastSuccess(str, _Url("http://example.com"))
        self.assertTryCastSuccess(str, "http://example.com")

    # === TypeVars ===

    def test_typevar(self) -> None:
        _T = TypeVar("_T")
        self.assertRaisesRegex(
            TypeNotSupportedError,
            "trycast cannot reliably determine whether value matches a TypeVar",
            lambda: trycast(Tuple[_T, _T], ("str", 123)),  # type: ignore[reportGeneralTypeIssues]  # pyright
        )

    # === Special Types: Any, Never, NoReturn ===

    def test_any(self) -> None:
        self.assertTryCastSuccess(Any, "words")
        self.assertTryCastSuccess(Any, 1)
        self.assertTryCastSuccess(Any, None)
        self.assertTryCastSuccess(Any, str)

    if sys.version_info >= (3, 11):

        def test_never(self) -> None:
            self.assertTryCastFailure(Never, "words")  # type: ignore[wrong-arg-types]  # pytype
            self.assertTryCastFailure(Never, 1)  # type: ignore[wrong-arg-types]  # pytype
            self.assertTryCastFailure(Never, None)  # type: ignore[wrong-arg-types]  # pytype
            self.assertTryCastFailure(Never, str)  # type: ignore[wrong-arg-types]  # pytype

            self.assertTryCastFailure(Never, ValueError)  # type: ignore[wrong-arg-types]  # pytype
            self.assertTryCastFailure(Never, ValueError())  # type: ignore[wrong-arg-types]  # pytype

    def test_noreturn(self) -> None:
        self.assertTryCastFailure(NoReturn, "words")  # type: ignore[wrong-arg-types]  # pytype
        self.assertTryCastFailure(NoReturn, 1)  # type: ignore[wrong-arg-types]  # pytype
        self.assertTryCastFailure(NoReturn, None)  # type: ignore[wrong-arg-types]  # pytype
        self.assertTryCastFailure(NoReturn, str)  # type: ignore[wrong-arg-types]  # pytype

        self.assertTryCastFailure(NoReturn, ValueError)  # type: ignore[wrong-arg-types]  # pytype
        self.assertTryCastFailure(NoReturn, ValueError())  # type: ignore[wrong-arg-types]  # pytype

    # === Forward References ===

    def test_typeddict_with_forwardrefs(self) -> None:
        self.assertTryCastSuccess(
            test_data.forwardrefs_example.Circle,
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

    def test_alias_to_union_with_forwardrefs(self) -> None:
        # Union with forward refs that have been resolved
        self.assertTryCastSuccess(
            eval_type(  # type: ignore[16]  # pyre
                test_data.forwardrefs_example.Shape,
                test_data.forwardrefs_example.__dict__,
                None,
            ),
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

        # Union with forward refs that have NOT been resolved
        self.assertRaisesRegex(
            UnresolvedForwardRefError,
            "contains a string-based forward reference",
            lambda: trycast(
                test_data.forwardrefs_example.Shape,
                dict(type="circle", center=dict(x=50, y=50), radius=25),
            ),
        )

        # Stringified reference to: Union with forward refs
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example.Shape",
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

    def test_alias_to_list_with_forwardrefs(self) -> None:
        # list with forward refs that have been resolved
        self.assertTryCastSuccess(
            eval_type(  # type: ignore[16]  # pyre
                test_data.forwardrefs_example.Scatterplot,
                test_data.forwardrefs_example.__dict__,
                None,
            ),
            [dict(x=50, y=50)],
        )

        # list with forward refs that have NOT been resolved
        self.assertRaisesRegex(
            UnresolvedForwardRefError,
            "contains a string-based forward reference",
            lambda: trycast(
                test_data.forwardrefs_example.Scatterplot, [dict(x=50, y=50)]
            ),
        )

        # Stringified reference to: list with forward refs
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example.Scatterplot", [dict(x=50, y=50)]
        )

    def test_alias_to_dict_with_forwardrefs(self) -> None:
        # dict with forward refs that have been resolved
        self.assertTryCastSuccess(
            eval_type(  # type: ignore[16]  # pyre
                test_data.forwardrefs_example.PointForLabel,
                test_data.forwardrefs_example.__dict__,
                None,
            ),
            {"Target": dict(x=50, y=50)},
        )

        # dict with forward refs that have NOT been resolved
        self.assertRaisesRegex(
            UnresolvedForwardRefError,
            "contains a string-based forward reference",
            lambda: trycast(
                test_data.forwardrefs_example.PointForLabel,
                {"Target": dict(x=50, y=50)},
            ),
        )

        # Stringified reference to: dict with forward refs
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example.PointForLabel",
            {"Target": dict(x=50, y=50)},
        )

    # === type Statement ===

    if sys.version_info >= (3, 12):

        def test_alias_to_union_defined_by_type_statement(self) -> None:
            import test_data.forwardrefs_example_with_type_statement

            # Union with forward refs with deferred resolution
            self.assertTryCastSuccess(
                test_data.forwardrefs_example_with_type_statement.Shape,
                dict(type="circle", center=dict(x=50, y=50), radius=25),
            )

        def test_alias_to_list_defined_by_type_statement(self) -> None:
            import test_data.forwardrefs_example_with_type_statement

            # list with forward refs with deferred resolution
            self.assertTryCastSuccess(
                test_data.forwardrefs_example_with_type_statement.Scatterplot,
                [dict(x=50, y=50)],
            )

        def test_alias_to_dict_with_forwardrefs(self) -> None:
            import test_data.forwardrefs_example_with_type_statement

            # dict with forward refs with deferred resolution
            self.assertTryCastSuccess(
                test_data.forwardrefs_example_with_type_statement.PointForLabel,
                {"Target": dict(x=50, y=50)},
            )

        def test_parameterized_alias(self) -> None:
            import test_data.type_statement_example

            self.assertTryCastSuccess(
                test_data.type_statement_example.FancyTuple[int, float],  # type: ignore[misc]  # mypy
                (1, 2.0),
            )
            self.assertTryCastSuccess(
                test_data.type_statement_example.FancyTuple,
                ("hello", "world"),
            )

            self.assertTryCastFailure(
                test_data.type_statement_example.FancyTuple[int, float],  # type: ignore[misc]  # mypy
                (1, "boom"),
            )

    # === Stringified References ===

    def test_stringified_reference(self) -> None:
        # builtin
        self.assertTryCastSuccess(
            "str",
            "hello",
        )

        if sys.version_info >= (3, 9):
            # builtin with builtin index expression
            self.assertTryCastSuccess(
                "list[int]",
                [1, 2],
            )

            # builtin with non-builtin index expression
            self.assertRaisesRegex(
                UnresolvableTypeError,
                "inside module 'builtins'.*?Try altering the type argument to be a string reference",
                lambda: trycast(
                    "list[List]",
                    [[1, 2], [3, 4]],
                ),
            )

        # List[]
        self.assertRaisesRegex(
            UnresolvableTypeError,
            "inside module 'builtins'.*?Try altering the type argument to be a string reference",
            lambda: trycast(
                "List",
                [1, 2],
            ),
        )

        # List[] with index expression
        self.assertRaisesRegex(
            UnresolvableTypeError,
            "inside module 'builtins'.*?Try altering the type argument to be a string reference",
            lambda: trycast(
                "List[int]",
                [1, 2],
            ),
        )

        # Reference to importable type with no forward references
        self.assertTryCastSuccess(
            "test_data.no_forwardrefs_example.Shape",
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

        # Reference to importable type with forward references
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example.Shape",
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

        # Reference to importable type that is a stringified TypeAlias
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example_with_import_annotations.Shape",
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

        # Reference to importable type with builtin index expression
        self.assertTryCastSuccess(
            "typing.List[int]",
            [1, 2],
        )

        # Reference to importable type with non-builtin index expression
        # residing in the same module
        self.assertTryCastSuccess(
            "typing.List[Any]",
            [1, 2],
        )

        # eval=False; stringified type as input
        self.assertRaisesRegex(
            UnresolvableTypeError,
            "appears to be a string reference.*?called with eval=False",
            lambda: trycast(
                "test_data.forwardrefs_example_with_import_annotations.Shape",
                dict(type="circle", center=dict(x=50, y=50), radius=25),
                eval=False,
            ),
        )

        # eval=False; ForwardRef() inside a TypedDict
        self.assertRaisesRegex(
            UnresolvedForwardRefError,
            "contains a string-based forward reference.*?called with eval=False",
            lambda: trycast(
                test_data.forwardrefs_example_with_import_annotations.Circle,
                dict(type="circle", center=dict(x=50, y=50), radius=25),
                eval=False,
            ),
        )

    # === from __future__ import annotations ===

    def test_types_defined_in_module_with_import_annotations(self) -> None:
        self.assertTryCastSuccess(
            test_data.forwardrefs_example_with_import_annotations.Circle,
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

        # Top-level stringified Union that has been resolved
        self.assertTryCastSuccess(
            eval(
                test_data.forwardrefs_example_with_import_annotations.Shape,
                test_data.forwardrefs_example_with_import_annotations.__dict__,
                None,
            ),
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

        # Top-level stringified Union that has NOT been resolved
        self.assertRaisesRegex(
            UnresolvableTypeError,
            "inside module 'builtins'.*?Try altering the type argument to be a string reference",
            lambda: trycast(
                test_data.forwardrefs_example_with_import_annotations.Shape,
                dict(type="circle", center=dict(x=50, y=50), radius=25),
            ),
        )

        # Stringified reference to: Top-level stringified Union
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example_with_import_annotations.Shape",
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

        # Top-level stringified List that has been resolved
        self.assertTryCastSuccess(
            eval(
                test_data.forwardrefs_example_with_import_annotations.Scatterplot,
                test_data.forwardrefs_example_with_import_annotations.__dict__,
                None,
            ),
            [dict(x=50, y=50)],
        )

        # Top-level stringified List that has NOT been resolved
        self.assertRaisesRegex(
            UnresolvableTypeError,
            "inside module 'builtins'.*?Try altering the type argument to be a string reference",
            lambda: trycast(
                test_data.forwardrefs_example_with_import_annotations.Scatterplot,
                [dict(x=50, y=50)],
            ),
        )

        # Stringified reference to: Top-level stringified List
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example_with_import_annotations.Scatterplot",
            [dict(x=50, y=50)],
        )

        # Top-level stringified Dict that has been resolved
        self.assertTryCastSuccess(
            eval(
                test_data.forwardrefs_example_with_import_annotations.PointForLabel,
                test_data.forwardrefs_example_with_import_annotations.__dict__,
                None,
            ),
            {"Target": dict(x=50, y=50)},
        )

        # Top-level stringified Dict that has NOT been resolved
        self.assertRaisesRegex(
            UnresolvableTypeError,
            "inside module 'builtins'.*?Try altering the type argument to be a string reference",
            lambda: trycast(
                test_data.forwardrefs_example_with_import_annotations.PointForLabel,
                {"Target": dict(x=50, y=50)},
            ),
        )

        # Stringified reference to: Top-level stringified Dict
        self.assertTryCastSuccess(
            "test_data.forwardrefs_example_with_import_annotations.PointForLabel",
            {"Target": dict(x=50, y=50)},
        )

    # === strict=True mode ===

    def test_rejects_mypy_typeddict_when_strict_is_true(self) -> None:
        class Point2D(mypy_extensions.TypedDict):  # type: ignore[reportGeneralTypeIssues]  # pyright
            x: int
            y: int

        class Point3D(Point2D, total=False):  # type: ignore[reportGeneralTypeIssues]  # pyright
            z: int

        self.assertRaisesRegex(
            TypeNotSupportedError,
            (
                "trycast cannot determine which keys are required.*?"
                "Suggest use a typing(_extensions)?.TypedDict.*?"
                "strict=False"
            ),
            lambda: trycast(Point3D, {"x": 1, "y": 2}, strict=True),
        )

    # NOTE: Cannot combine the following two if-checks with an `and`
    #       because that is too complicated for Pyre to understand.
    #
    #       For more info about the forms that Pyre supports, see its tests:
    #       https://github.com/facebook/pyre-check/blob/ee6d16129c112fb1feb1435a245d5e6a114e58d9/analysis/test/preprocessingTest.ml#L626
    if sys.version_info >= (3, 8):
        if sys.version_info < (3, 9):

            def test_rejects_python_3_8_typeddict_when_strict_is_true(self) -> None:
                class Point2D(typing.TypedDict):  # type: ignore[not-supported-yet]  # pytype
                    x: int
                    y: int

                class Point3D(Point2D, total=False):
                    z: int

                self.assertRaisesRegex(
                    TypeNotSupportedError,
                    (
                        "trycast cannot determine which keys are required.*?"
                        "Suggest use a typing(_extensions)?.TypedDict.*?"
                        "strict=False"
                    ),
                    lambda: trycast(Point3D, {"x": 1, "y": 2}, strict=True),
                )

    # === strict=False mode ===

    def test_accepts_mypy_typeddict_when_strict_is_false(self) -> None:
        class Point2D(mypy_extensions.TypedDict):  # type: ignore[reportGeneralTypeIssues]  # pyright
            x: int
            y: int

        # NOTE: mypy_extensions.TypedDict doesn't preserve at runtime
        #       which of Point3D's inherited fields from Point2D are required.
        #       So trycast() guesses (incorrectly) that ALL fields of Point3D
        #       are not-required because Point3D is declared as total=False.
        class Point3D(Point2D, total=False):  # type: ignore[reportGeneralTypeIssues]  # pyright
            z: int

        class MaybePoint1D(mypy_extensions.TypedDict, total=False):  # type: ignore[reportGeneralTypeIssues]  # pyright
            x: int

        class TaggedMaybePoint1D(MaybePoint1D):
            name: str

        self.assertTryCastSuccess(Point2D, {"x": 1, "y": 2}, strict=False)
        self.assertTryCastFailure(Point2D, {"x": 1, "y": "string"}, strict=False)
        self.assertTryCastFailure(Point2D, {"x": 1}, strict=False)

        self.assertTryCastSuccess(Point3D, {"x": 1, "y": 2, "z": 3}, strict=False)
        self.assertTryCastFailure(
            Point3D, {"x": 1, "y": 2, "z": "string"}, strict=False
        )
        self.assertTryCastSuccess(Point3D, {"x": 1, "y": 2}, strict=False)
        self.assertTryCastSuccess(Point3D, {"x": 1}, strict=False)  # surprise!
        self.assertTryCastSuccess(Point3D, {"q": 1}, strict=False)  # surprise!

        self.assertTryCastSuccess(MaybePoint1D, {"x": 1}, strict=False)
        self.assertTryCastFailure(MaybePoint1D, {"x": "string"}, strict=False)
        self.assertTryCastSuccess(MaybePoint1D, {}, strict=False)
        self.assertTryCastSuccess(MaybePoint1D, {"q": 1}, strict=False)  # surprise!

        self.assertTryCastSuccess(
            TaggedMaybePoint1D, {"x": 1, "name": "one"}, strict=False
        )
        self.assertTryCastFailure(
            TaggedMaybePoint1D, {"name": "one"}, strict=False
        )  # surprise!

    # NOTE: Cannot combine the following two if-checks with an `and`
    #       because that is too complicated for Pyre to understand.
    #
    #       For more info about the forms that Pyre supports, see its tests:
    #       https://github.com/facebook/pyre-check/blob/ee6d16129c112fb1feb1435a245d5e6a114e58d9/analysis/test/preprocessingTest.ml#L626
    if sys.version_info >= (3, 8):
        if sys.version_info < (3, 9):

            def test_accepts_python_3_8_typeddict_when_strict_is_false(self) -> None:
                class Point2D(typing.TypedDict):  # type: ignore[not-supported-yet]  # pytype
                    x: int
                    y: int

                # NOTE: typing.TypedDict in Python 3.8 doesn't preserve at runtime
                #       which of Point3D's inherited fields from Point2D are required.
                #       So trycast() guesses (incorrectly) that ALL fields of Point3D
                #       are not-required because Point3D is declared as total=False.
                class Point3D(Point2D, total=False):
                    z: int

                class MaybePoint1D(typing.TypedDict, total=False):  # type: ignore[not-supported-yet]  # pytype
                    x: int

                class TaggedMaybePoint1D(MaybePoint1D):
                    name: str

                self.assertTryCastSuccess(Point2D, {"x": 1, "y": 2}, strict=False)
                self.assertTryCastFailure(Point2D, {"x": 1}, strict=False)

                self.assertTryCastSuccess(
                    Point3D, {"x": 1, "y": 2, "z": 3}, strict=False
                )
                self.assertTryCastSuccess(Point3D, {"x": 1, "y": 2}, strict=False)
                self.assertTryCastSuccess(Point3D, {"x": 1}, strict=False)  # surprise!
                # NOTE: Unknown keys are allowed
                self.assertTryCastSuccess(Point3D, {"q": 1}, strict=False)

                self.assertTryCastSuccess(MaybePoint1D, {"x": 1}, strict=False)
                self.assertTryCastSuccess(MaybePoint1D, {}, strict=False)
                # NOTE: Unknown keys are allowed
                self.assertTryCastSuccess(MaybePoint1D, {"q": 1}, strict=False)

                self.assertTryCastSuccess(
                    TaggedMaybePoint1D, {"x": 1, "name": "one"}, strict=False
                )
                self.assertTryCastFailure(
                    TaggedMaybePoint1D, {"name": "one"}, strict=False
                )  # surprise!

    # === Misuse: Nice Error Messages ===

    def test_tuple_of_types(self) -> None:
        self.assertRaisesRegex(
            TypeError,
            "does not support checking against a tuple of types",
            lambda: trycast((int, str), 1),
        )

    # NOTE: The internal _type_check function is heavily exercised by this test.
    def test_reversing_order_of_first_two_arguments_gives_nice_error_message(
        self,
    ) -> None:
        CASES = [
            (int, 1),
            (bool, True),
            (list, [1, 2]),
            (dict, {"x": 1, "y": 2}),
        ]

        for tp, value in CASES:
            with self.subTest(tp=tp):
                self.assertEqual(value, trycast(tp, value))
                self.assertRaisesRegex(
                    TypeError,
                    "requires a type as its first argument",
                    lambda: trycast(value, tp),
                )

    # === Large Examples ===

    def test_shape_endpoint_parsing_example(self) -> None:
        x1 = dict(type="circle", center=dict(x=50, y=50), radius=25)
        xA = dict(type="circle", center=dict(x=50, y=50))
        x2 = dict(type="rect", x=10, y=20, width=50, height=50)
        xB = dict(type="rect", width=50, height=50)
        xC = dict(type="oval", x=10, y=20, width=50, height=50)

        draw_shape_endpoint(x1)
        draw_shape_endpoint(xA)
        draw_shape_endpoint(x2)
        draw_shape_endpoint(xB)
        draw_shape_endpoint(xC)

        self.assertEqual(
            [
                x1,
                HTTP_400_BAD_REQUEST,
                x2,
                HTTP_400_BAD_REQUEST,
                HTTP_400_BAD_REQUEST,
            ],
            shapes_drawn,
        )

    # === Missing Typing Extensions ===

    def test_can_import_and_use_trycast_even_if_typing_extensions_unavailable(
        self,
    ) -> None:
        with self._typing_extensions_not_importable():
            with self._trycast_reimported():
                self.assertTryCastSuccess(int, 1)
                self.assertTryCastSuccess(str, "alpha")

                self.assertTryCastFailure(str, 1)
                self.assertTryCastFailure(int, "alpha")

    @contextmanager
    def _typing_extensions_not_importable(self) -> Iterator[None]:
        old_te_module = sys.modules["typing_extensions"]
        del sys.modules["typing_extensions"]
        try:
            old_meta_path = sys.meta_path  # capture
            te_gone_loader = _TypingExtensionsGoneLoader()  # type: MetaPathFinder

            # The cast is necessary to ignore 'assignment error' invoked in mypy 0.910.
            sys.meta_path = cast(List, [te_gone_loader]) + sys.meta_path
            try:
                try:
                    import typing_extensions
                except ImportError:
                    pass  # good
                else:
                    raise AssertionError(  # pragma: no cover
                        "Failed to make typing_extensions unimportable"
                    )

                yield
            finally:
                sys.meta_path = old_meta_path
        finally:
            sys.modules["typing_extensions"] = old_te_module

    @contextmanager
    def _trycast_reimported(self):
        old_tc_module = sys.modules["trycast"]
        del sys.modules["trycast"]
        try:
            old_tc = globals()["trycast"]
            del globals()["trycast"]
            try:
                from trycast import trycast

                globals()["trycast"] = trycast

                yield
            finally:
                globals()["trycast"] = old_tc
        finally:
            sys.modules["trycast"] = old_tc_module

    # === Utility ===

    def assertTryCastSuccess(
        self, tp: object, value: object, *, strict: Optional[bool] = None
    ) -> None:
        kwargs = dict(strict=strict) if strict is not None else dict()
        self.assertIs(
            value,
            trycast(tp, value, **kwargs),
            f"Expected trycast({tp}, {value}) to SUCCEED",
        )

    def assertTryCastFailure(
        self, tp: object, value: object, *, strict: Optional[bool] = None
    ) -> None:
        kwargs = dict(strict=strict) if strict is not None else dict()
        self.assertIs(
            None,
            trycast(tp, value, **kwargs),
            f"Expected trycast({tp}, {value}) to FAIL",
        )

    def assertTryCastNoneSuccess(self, tp: object) -> None:
        self.assertIs(None, trycast(tp, None, _FAILURE))


class _TypingExtensionsGoneLoader(MetaPathFinder):
    def find_spec(self, module_name, parent_path, old_module_object=None):
        if module_name == "typing_extensions" and parent_path is None:
            raise ModuleNotFoundError
        return None


# ------------------------------------------------------------------------------
# API: TestCheckCast


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


class TestCheckCast(TestCase):
    """
    Tests checkcast()-specific ValidationErrors.

    For testing of checkcast()'s typechecking behavior, see the TestTryCast suite.

    Duplicate suite structures are used by TestCheckCast and TestTryCast,
    so it's useful to update both suites at the same time.
    """

    # Enable unlimited diffs in assertion failures
    maxDiff = None

    # === Scalars ===

    def test_simple_scalar(self) -> None:
        # Actual bools
        checkcast(bool, True)
        checkcast(bool, False)

        # Not actual bools
        self.assertRaisesEqual(
            ValidationError,
            "Expected bool but found 'True'",
            lambda: checkcast(bool, "True"),
        )

    def test_none(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected NoneType but found 1",
            lambda: checkcast(None, 1),
        )
        checkcast(None, None)

    def test_none_type(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected NoneType but found 1",
            lambda: checkcast(type(None), 1),
        )
        checkcast(type(None), None)

    # === Strings ===

    def test_str(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected str but found 1",
            lambda: checkcast(str, 1),
        )

    # === Raw Collections ===

    def test_list(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected list but found None",
            lambda: checkcast(list, None),
        )

    def test_big_list(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected list but found None",
            lambda: checkcast(List, None),
        )

    # === Generic Collections ===

    if sys.version_info >= (3, 9):

        def test_list_t(self) -> None:
            self.assertRaisesEqual(
                ValidationError,
                "Expected list[int] but found None",
                lambda: checkcast(list[int], None),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected list[int] but found ['1']
                      At index 0: Expected int but found '1'
                    """.rstrip()
                ),
                lambda: checkcast(list[int], ["1"]),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected list[int] but found [0, 1, None, 3, None, 5]
                      At index 2: Expected int but found None
                    """.rstrip()
                ),
                lambda: checkcast(list[int], [0, 1, None, 3, None, 5]),
            )

    def test_big_list_t(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected list[int] but found None",
            lambda: checkcast(List[int], None),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected list[int] but found ['1']
                  At index 0: Expected int but found '1'
                """.rstrip()
            ),
            lambda: checkcast(List[int], ["1"]),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected list[int] but found [0, 1, None, 3, None, 5]
                  At index 2: Expected int but found None
                """.rstrip()
            ),
            lambda: checkcast(List[int], [0, 1, None, 3, None, 5]),
        )

    if sys.version_info >= (3, 9):

        def test_tuple_t_ellipsis(self) -> None:
            # non-tuple[T, ...]s
            self.assertRaisesEqual(
                ValidationError,
                "Expected tuple[int, ...] but found None",
                lambda: checkcast(tuple[int, ...], None),  # type: ignore[6]  # pyre
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected tuple[int, ...] but found ('1',)
                      At index 0: Expected int but found '1'
                    """.rstrip()
                ),
                lambda: checkcast(tuple[int, ...], ("1",)),  # type: ignore[6]  # pyre
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected tuple[int, ...] but found (0, 1, None, 3, None, 5)
                      At index 2: Expected int but found None
                    """.rstrip()
                ),
                lambda: checkcast(tuple[int, ...], (0, 1, None, 3, None, 5)),  # type: ignore[6]  # pyre
            )

    def test_big_tuple_t_ellipsis(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected tuple[int, ...] but found None",
            lambda: checkcast(Tuple[int, ...], None),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected tuple[int, ...] but found ('1',)
                  At index 0: Expected int but found '1'
                """.rstrip()
            ),
            lambda: checkcast(Tuple[int, ...], ("1",)),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected tuple[int, ...] but found (0, 1, None, 3, None, 5)
                  At index 2: Expected int but found None
                """.rstrip()
            ),
            lambda: checkcast(Tuple[int, ...], (0, 1, None, 3, None, 5)),
        )

    if sys.version_info >= (3, 9):

        def test_dict_k_v(self) -> None:
            self.assertRaisesEqual(
                ValidationError,
                "Expected dict[str, int] but found None",
                lambda: checkcast(dict[str, int], None),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected dict[int, str] but found {'1': 'foo'}
                      Key '1': Expected int but found '1'
                    """.rstrip()
                ),
                lambda: checkcast(dict[int, str], {"1": "foo"}),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected dict[int, str] but found {1: 'foo', '900': 'foo', 2: 'foo', '901': 'foo'}
                      Key '900': Expected int but found '900'
                    """.rstrip()
                ),
                lambda: checkcast(
                    dict[int, str], {1: "foo", "900": "foo", 2: "foo", "901": "foo"}
                ),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected dict[int, str] but found {1: 999}
                      At key 1: Expected str but found 999
                    """.rstrip()
                ),
                lambda: checkcast(dict[int, str], {1: 999}),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected dict[int, str] but found {1: 'foo', 2: 900, 3: 'foo', 4: 901}
                      At key 2: Expected str but found 900
                    """.rstrip()
                ),
                lambda: checkcast(dict[int, str], {1: "foo", 2: 900, 3: "foo", 4: 901}),
            )

    def test_big_dict_k_v(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected dict[str, int] but found None",
            lambda: checkcast(Dict[str, int], None),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected dict[int, str] but found {'1': 'foo'}
                  Key '1': Expected int but found '1'
                """.rstrip()
            ),
            lambda: checkcast(Dict[int, str], {"1": "foo"}),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected dict[int, str] but found {1: 'foo', '900': 'foo', 2: 'foo', '901': 'foo'}
                  Key '900': Expected int but found '900'
                """.rstrip()
            ),
            lambda: checkcast(
                Dict[int, str], {1: "foo", "900": "foo", 2: "foo", "901": "foo"}
            ),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected dict[int, str] but found {1: 999}
                  At key 1: Expected str but found 999
                """.rstrip()
            ),
            lambda: checkcast(Dict[int, str], {1: 999}),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected dict[int, str] but found {1: 'foo', 2: 900, 3: 'foo', 4: 901}
                  At key 2: Expected str but found 900
                """.rstrip()
            ),
            lambda: checkcast(Dict[int, str], {1: "foo", 2: 900, 3: "foo", 4: 901}),
        )

    # === TypedDicts ===

    def test_typeddict(self) -> None:
        class Point2D(RichTypedDict):
            x: int
            y: int

        class PartialPoint2D(RichTypedDict, total=False):
            x: int
            y: int

        class Point3D(RichTypedDict):
            x: int
            y: int
            z: int

        # Point2D
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected Point2D but found {'x': 1}
                  Required key 'y' is missing
                """.rstrip()
            ),
            lambda: checkcast(Point2D, {"x": 1}),
        )
        checkcast(Point2D, {"x": 1, "y": 1})
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected Point2D but found {'x': 1, 'y': 'string'}
                  At key 'y': Expected int but found 'string'
                """.rstrip()
            ),
            lambda: checkcast(Point2D, {"x": 1, "y": "string"}),
        )
        checkcast(Point2D, {"x": 1, "y": 1, "z": 1})
        checkcast(Point2D, {"x": 1, "y": 1, "z": "string"})

        # PartialPoint2D
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected PartialPoint2D but found {'x': 1, 'y': 'string'}
                  At key 'y': Expected int but found 'string'
                """.rstrip()
            ),
            lambda: checkcast(PartialPoint2D, {"x": 1, "y": "string"}),
        )

        # Point3D
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected Point3D but found {'x': 1, 'y': 1}
                  Required key 'z' is missing
                """.rstrip()
            ),
            lambda: checkcast(Point3D, {"x": 1, "y": 1}),
        )

    # === Tuples (Heterogeneous) ===

    if sys.version_info >= (3, 9):

        def test_tuple_ts(self) -> None:
            self.assertRaisesEqual(
                ValidationError,
                "Expected tuple[int] but found None",
                lambda: checkcast(tuple[int], None),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected tuple[int] but found ('A',)
                      At index 0: Expected int but found 'A'
                    """.rstrip()
                ),
                lambda: checkcast(tuple[int], ("A",)),
            )
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected tuple[int, str] but found (1, 2)
                      At index 1: Expected str but found 2
                    """.rstrip()
                ),
                lambda: checkcast(tuple[int, str], (1, 2)),  # type: ignore[6]  # pyre
            )

    def test_big_tuple_ts(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            "Expected tuple[int] but found None",
            lambda: checkcast(Tuple[int], None),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected tuple[int] but found ('A',)
                  At index 0: Expected int but found 'A'
                """.rstrip()
            ),
            lambda: checkcast(Tuple[int], ("A",)),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected tuple[int, str] but found (1, 2)
                  At index 1: Expected str but found 2
                """.rstrip()
            ),
            lambda: checkcast(Tuple[int, str], (1, 2)),
        )

    # === Unions ===

    def test_union(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages(
                dedent(
                    """\
                    Expected Union[int, str] but found None
                      Expected int but found None
                      Expected str but found None
                    """.rstrip()
                )
            ),
            lambda: checkcast(Union[int, str], None),
        )
        checkcast(Union[int, str], "words")

    def test_optional(self) -> None:
        # NOTE: It would be nicer if Optional[T] was preserved
        #       and NOT converted to Union[T, NoneType]
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages(
                dedent(
                    """\
                    Expected Union[str, NoneType] but found 1
                      Expected str but found 1
                      Expected NoneType but found 1
                    """.rstrip()
                )
            ),
            lambda: checkcast(Optional[str], 1),
        )
        checkcast(Optional[str], "words")
        checkcast(Optional[str], None)

    if sys.version_info >= (3, 10):

        def test_uniontype(self) -> None:
            self.assertRaisesEqual(
                ValidationError,
                dedent(
                    """\
                    Expected int | str but found None
                      Expected int but found None
                      Expected str but found None
                    """.rstrip()
                ),
                lambda: checkcast(int | str, None),
            )
            checkcast(int | str, "words")

    # === Literals ===

    def test_literal(self) -> None:
        # Literal-like with the wrong value
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages(
                "Expected Literal['circle'] but found 'square'"
            ),
            lambda: checkcast(Literal["circle"], "square"),
        )
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages("Expected Literal[1] but found 2"),
            lambda: checkcast(Literal[1], 2),
        )

        # non-Literal
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages("Expected Literal['circle'] but found None"),
            lambda: checkcast(Literal["circle"], None),
        )
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages("Expected Literal['circle'] but found 0"),
            lambda: checkcast(Literal["circle"], 0),
        )

    # === Special Types: Any, Never, NoReturn ===

    if sys.version_info >= (3, 11):

        def test_never(self) -> None:
            self.assertRaisesEqual(
                ValidationError,
                "Expected Never but found None",
                lambda: checkcast(Never, None),
            )

    def test_noreturn(self) -> None:
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages("Expected NoReturn but found None"),
            lambda: checkcast(NoReturn, None),
        )

    # === Large Examples ===

    def test_http_request_parsing_example(self) -> None:
        checkcast(
            _ProxiedHttpRequestEnvelope,
            {
                "request": {
                    "url": "https://example.com/",
                    "method": "GET",
                    "headers": {},
                    "content": {"type": None, "text": ""},
                }
            },
        )
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages(
                dedent(
                    """\
                    Expected _ProxiedHttpRequestEnvelope but found {'request': {'url': 'https://example.com/', 'method': 'BREW', 'headers': {}, 'content': {'type': None, 'text': ''}}}
                      At key 'request': Expected _ProxiedHttpRequest but found {'url': 'https://example.com/', 'method': 'BREW', 'headers': {}, 'content': {'type': None, 'text': ''}}
                        At key 'method': Expected Literal['DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT'] but found 'BREW'
                    """.rstrip()
                )
            ),
            lambda: checkcast(
                _ProxiedHttpRequestEnvelope,
                {
                    "request": {
                        "url": "https://example.com/",
                        "method": "BREW",
                        "headers": {},
                        "content": {"type": None, "text": ""},
                    }
                },
            ),
        )

        checkcast(
            _ProxiedHttpRequestEnvelope,
            {
                "request": {
                    "url": "https://example.com/api/posts",
                    "method": "GET",
                    "headers": {},
                    "content": {
                        "type": {
                            "family": "application/json",
                            "value": "application/json",
                        },
                        "text": '{"offset": 0, "limit": 20}',
                    },
                }
            },
        )
        self.assertRaisesEqual(
            ValidationError,
            self._typing_error_messages(
                dedent(
                    """\
                    Expected _ProxiedHttpRequestEnvelope but found {'request': {'url': 'https://example.com/api/posts', 'method': 'GET', 'headers': {}, 'content': {'type': {'value': 'application/json'}, 'text': '{"offset": 0, "limit": 20}'}}}
                      At key 'request': Expected _ProxiedHttpRequest but found {'url': 'https://example.com/api/posts', 'method': 'GET', 'headers': {}, 'content': {'type': {'value': 'application/json'}, 'text': '{"offset": 0, "limit": 20}'}}
                        At key 'content': Expected _ProxiedHttpContent but found {'type': {'value': 'application/json'}, 'text': '{"offset": 0, "limit": 20}'}
                          At key 'type': Expected Union[_HttpContentTypeDescriptor, NoneType] but found {'value': 'application/json'}
                            Expected _HttpContentTypeDescriptor but found {'value': 'application/json'}
                              Required key 'family' is missing
                            Expected NoneType but found {'value': 'application/json'}
                    """.rstrip()
                )
            ),
            lambda: checkcast(
                _ProxiedHttpRequestEnvelope,
                {
                    "request": {
                        "url": "https://example.com/api/posts",
                        "method": "GET",
                        "headers": {},
                        "content": {
                            "type": {"value": "application/json"},
                            "text": '{"offset": 0, "limit": 20}',
                        },
                    }
                },
            ),
        )
        self.assertRaisesEqual(
            ValidationError,
            dedent(
                """\
                Expected _ProxiedHttpRequestEnvelope but found {'request': {'url': 'https://example.com/api/posts', 'method': 'GET', 'headers': {}, 'content': {'type': {'family': 'application/json', 'value': 'application/json'}, 'text': None}}}
                  At key 'request': Expected _ProxiedHttpRequest but found {'url': 'https://example.com/api/posts', 'method': 'GET', 'headers': {}, 'content': {'type': {'family': 'application/json', 'value': 'application/json'}, 'text': None}}
                    At key 'content': Expected _ProxiedHttpContent but found {'type': {'family': 'application/json', 'value': 'application/json'}, 'text': None}
                      At key 'text': Expected str but found None
                """.rstrip()
            ),
            lambda: checkcast(
                _ProxiedHttpRequestEnvelope,
                {
                    "request": {
                        "url": "https://example.com/api/posts",
                        "method": "GET",
                        "headers": {},
                        "content": {
                            "type": {
                                "family": "application/json",
                                "value": "application/json",
                            },
                            "text": None,
                        },
                    }
                },
            ),
        )

    # === Misc ===

    def test_checkcast_returns_value_of_correct_type(self) -> None:
        input = True
        output = checkcast(bool, input)
        if sys.version_info >= (3, 11):
            from typing import assert_type

            assert_type(output, bool)  # NOT: bool | None

    # === Utility ===

    def assertRaisesEqual(
        self, tp: Type[BaseException], msg: Union[str, List[str]], callable: Callable
    ) -> None:
        try:
            callable()
        except tp as e:
            if isinstance(msg, str):
                expected_values = [msg]
            else:
                expected_values = msg
            if (actual_value := str(e)) not in expected_values:
                # Raise AssertionError with better message
                self.assertEqual(expected_values[0], actual_value)
        else:
            self.fail(f"Expected {tp}")

    @staticmethod
    def _typing_error_messages(template: str) -> List[str]:
        python_lt_3_9 = (
            template.replace("Literal", "typing.Literal")
            .replace("NoReturn", "typing.NoReturn")
            .replace("Union", "typing.Union")
        )
        return [
            template,
            python_lt_3_9,  # for Python <=3.9
        ]


class TestValidationError(TestCase):
    """
    Tests the ValidationError class.
    """

    def test_validation_error_api_is_only_two_arg_constructor_and_str(self) -> None:
        # Ensure can create ValidationError with (tp, value)
        e = ValidationError(str, None)

        # Ensure can get str() of ValidationError
        self.assertEqual("Expected str but found None", str(e))

        # Ensure non-dunder API attributes match expected set
        if True:
            standard_e = Exception()
            standard_e_api = [x for x in dir(standard_e) if not x.startswith("_")]

            expected_api = [
                # nothing
            ]  # type: List[str]
            actual_api = [
                x for x in dir(e) if not x.startswith("_") and x not in standard_e_api
            ]
            self.assertEqual(expected_api, actual_api)

    def test_validation_error_is_value_error(self) -> None:
        self.assertTrue(issubclass(ValidationError, ValueError))


# ------------------------------------------------------------------------------
# API: TestIsAssignable


class _Cell(RichTypedDict):
    value: object


class TestIsAssignable(TestCase):
    """
    Tests whether the isassignable() function works.
    """

    def test_is_similar_to_isinstance(self) -> None:
        self.assertTrue(isassignable("words", str))
        self.assertTrue(isassignable(1, int))
        self.assertTrue(isassignable(True, bool))

        self.assertFalse(isassignable("words", int))
        self.assertFalse(isassignable(1, str))
        self.assertFalse(isassignable(True, str))

    def test_is_different_from_isinstance_where_pep_484_differs(self) -> None:
        self.assertTrue(isassignable(True, int))
        self.assertTrue(isassignable(1, float))
        self.assertTrue(isassignable(1.0, complex))

    def test_return_type_is_typeguarded_positively_for_types(self) -> None:
        value = "words"
        if isassignable(value, str):
            self._demands_a_str(value)  # ensure typechecks

    @staticmethod
    def _demands_a_str(value: str) -> str:
        return value

    # TODO: Add support for this case when TypeForm is implemented
    #       (and it interacts with TypeGuard correctly). See:
    #       https://github.com/python/mypy/issues/9773
    # def test_return_type_is_typeguarded_positively_for_typeforms(self) -> None:
    #    value = {"value": "contents"}
    #    if isassignable(value, _Cell):
    #        self._demands_a_typeddict(value)  # ensure typechecks
    #
    # @staticmethod
    # def _demands_a_typeddict(cell: _Cell) -> object:
    #    return cell["value"]

    # TODO: Add support for this case if/when support for a "strict" TypeGuard
    #       of some kind is introduced that narrows in the negative case.
    # def test_return_type_is_typeguarded_negatively(self) -> None:
    #    value = 'words'
    #    if not isassignable(value, str):
    #        self._demands_a_never(value)  # ensure typechecks
    #
    # @staticmethod
    # def _demands_a_never(value: NoReturn) -> NoReturn:  # type: ignore[invalid-annotation]  # pytype
    #    raise ValueError("expected this code to be unreachable")


# ------------------------------------------------------------------------------
# Internal: TestIsTypedDict

from typing import (
    TypedDict as TypingTypedDict,  # type: ignore[not-supported-yet]  # pytype
)

from trycast import _is_typed_dict


class TypingPoint(TypingTypedDict):
    x: int
    y: int


from typing_extensions import (
    TypedDict as TypingExtensionsTypedDict,  # type: ignore[not-supported-yet]  # pytype
)


class TypingExtensionsPoint(TypingExtensionsTypedDict):
    x: int
    y: int


class MypyExtensionsPoint(mypy_extensions.TypedDict):  # type: ignore[reportGeneralTypeIssues]  # pyright
    x: int
    y: int


class TestIsTypedDict(TestCase):
    """
    Tests whether the _is_typed_dict() internal function works.
    """

    def test_recognizes_typed_dict_from_typing(self) -> None:
        self.assertTrue(_is_typed_dict(TypingPoint))

    def test_recognizes_typed_dict_from_typing_extensions(self) -> None:
        self.assertTrue(_is_typed_dict(TypingExtensionsPoint))

    def test_recognizes_typed_dict_from_mypy_extensions(self) -> None:
        self.assertTrue(_is_typed_dict(MypyExtensionsPoint))


# ------------------------------------------------------------------------------
# Meta: TestTypechecks

_P = ParamSpec("_P")


def _tag(tag_name: str) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:  # type: ignore[34]  # pyre
    """
    Adds a tag to a test method, so that it can be skipped using the
    TRYCAST_SKIP_TEST_TAGS environment variable.

    Examples:
        $ TRYCAST_SKIP_TEST_TAGS=pyright,pyre make test
    or
        $ TRYCAST_SKIP_TEST_TAGS=pyright,pyre python -m unittest
    """

    def decorate(f: Callable[_P, _R]) -> Callable[_P, _R]:
        def decorated(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            if tag_name in os.environ.get("TRYCAST_SKIP_TEST_TAGS", "").split(","):
                raise SkipTest(f"skipping test tagged {tag_name}")
            return f(*args, **kwargs)

        return decorated

    return decorate


class TestTypechecks(TestCase):
    @_tag("mypy")
    def test_no_mypy_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["mypy"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:  # pragma: no cover
            self.fail(
                f'mypy typechecking failed:\n\n{e.output.decode("utf-8").strip()}'
            )

    # TODO: This test runs very slowly (4.8 seconds on @davidfstr's laptop).
    #       Investigate way to configure pyright to have a faster startup time.
    @_tag("pyright")
    def test_no_pyright_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["pyright"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:  # pragma: no cover
            self.fail(
                f'pyright typechecking failed:\n\n{e.output.decode("utf-8").strip()}'
            )

    @_tag("pyre")
    def test_no_pyre_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["pyre", "check"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:  # pragma: no cover
            output_str = e.output.decode("utf-8").strip()

            # Don't run pyre during automated tests on macOS 10.14
            # because pyre won't run on that macOS version.
            # See: https://github.com/facebook/pyre-check/issues/545
            if "___darwin_check_fd_set_overflow" in output_str and platform.mac_ver()[
                0
            ].startswith("10.14."):
                self.skipTest("Cannot run Pyre on macOS 10.14")
                return

            self.fail(f"pyre typechecking failed:\n\n{output_str}")

    @_tag("pytype")
    def test_no_pytype_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["pytype", "--keep-going", "trycast/__init__.py", "tests.py"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:  # pragma: no cover
            self.fail(
                f'pytype typechecking failed:\n\n{e.output.decode("utf-8").strip()}'
            )
        except FileNotFoundError:
            if sys.version_info >= (3, 10):
                self.skipTest("Cannot run pytype on Python 3.10+")
            else:  # pragma: no cover
                raise


# ------------------------------------------------------------------------------
