# flake8: noqa
import os
import platform
import subprocess
import sys
import typing
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)
from unittest import TestCase

import mypy_extensions

import test_data.forwardrefs_example

if sys.version_info >= (3, 7):
    import test_data.forwardrefs_example_with_import_annotations

from tests_shape_example import HTTP_400_BAD_REQUEST, draw_shape_endpoint, shapes_drawn
from trycast import (
    TypeNotSupportedError,
    UnresolvableTypeError,
    UnresolvedForwardRefError,
    isassignable,
    trycast,
)

# Literal
if sys.version_info >= (3, 8):
    from typing import Literal  # Python 3.8+
else:
    from typing_extensions import Literal  # Python 3.5+

# TypedDict
if sys.version_info >= (3, 8):
    from typing import TypedDict  # Python 3.8+
else:
    from typing_extensions import TypedDict  # Python 3.5+

from typing import _eval_type as eval_type  # type: ignore  # private API not in stubs

_FAILURE = object()


class _Movie(TypedDict):
    name: str
    year: int


class _BookBasedMovie(_Movie):
    based_on: str


class _MaybeBookBasedMovie(_Movie, total=False):
    based_on: str


class _MaybeMovie(TypedDict, total=False):
    name: str
    year: int


class _BookBasedMaybeMovie(_MaybeMovie):
    based_on: str


class X(TypedDict):
    x: int


class Y(TypedDict):
    y: str


class XYZ(X, Y):
    z: bool


class TestTryCast(TestCase):
    # === Scalars ===

    def test_bool(self) -> None:
        # Actual bools
        self.assertTryCastSuccess(bool, True)
        self.assertTryCastSuccess(bool, False)

        # bool-like ints
        self.assertTryCastFailure(bool, 0)
        self.assertTryCastFailure(bool, 1)

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

        # int-like bools
        self.assertTryCastFailure(int, False)
        self.assertTryCastFailure(int, True)

        # int-like floats
        self.assertTryCastFailure(int, 0.0)
        self.assertTryCastFailure(int, 1.0)
        self.assertTryCastFailure(int, -1.0)

        # int-like strs
        self.assertTryCastFailure(int, "0")
        self.assertTryCastFailure(int, "1")
        self.assertTryCastFailure(int, "-1")

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

        # float-like bools
        self.assertTryCastFailure(float, False)
        self.assertTryCastFailure(float, True)

        # float-like strs
        self.assertTryCastFailure(float, "1.0")
        self.assertTryCastFailure(float, "inf")
        self.assertTryCastFailure(float, "Infinity")

        # int-like bools
        self.assertTryCastFailure(float, False)
        self.assertTryCastFailure(float, True)

        # int-like strs
        self.assertTryCastFailure(float, "0")
        self.assertTryCastFailure(float, "1")
        self.assertTryCastFailure(float, "-1")

        # non-floats
        self.assertTryCastFailure(float, "foo")
        self.assertTryCastFailure(float, [1])
        self.assertTryCastFailure(float, {1: 1})
        self.assertTryCastFailure(float, {1})
        self.assertTryCastFailure(float, object())

        # non-ints
        self.assertTryCastFailure(float, "foo")
        self.assertTryCastFailure(float, [1])
        self.assertTryCastFailure(float, {1: 1})
        self.assertTryCastFailure(float, {1})
        self.assertTryCastFailure(float, object())

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

            # list[T]-like lists
            self.assertTryCastFailure(list[int], [True])
            self.assertTryCastFailure(list[int], [1, True])

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

        # list[T]-like lists
        self.assertTryCastFailure(List[int], [True])
        self.assertTryCastFailure(List[int], [1, True])

        # non-list[T]s
        self.assertTryCastFailure(List[int], 0)
        self.assertTryCastFailure(List[int], "foo")
        self.assertTryCastFailure(List[int], ["1"])
        self.assertTryCastFailure(List[int], {1: 1})
        self.assertTryCastFailure(List[int], {1})
        self.assertTryCastFailure(List[int], object())

    if sys.version_info >= (3, 9):

        def test_tuple_t_ellipsis(self) -> None:
            # Actual tuple[T, ...]
            self.assertTryCastSuccess(tuple[int, ...], ())  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(tuple[int, ...], (1,))  # type: ignore[6]  # pyre
            self.assertTryCastSuccess(tuple[int, ...], (1, 2))  # type: ignore[6]  # pyre

            # tuple[T, ...]-like tuples
            self.assertTryCastFailure(tuple[int, ...], (True,))  # type: ignore[6]  # pyre
            self.assertTryCastFailure(tuple[int, ...], (1, True))  # type: ignore[6]  # pyre

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

        # tuple[T, ...]-like tuples
        self.assertTryCastFailure(Tuple[int, ...], (True,))
        self.assertTryCastFailure(Tuple[int, ...], (1, True))

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

        # Sequence[T]-like lists
        self.assertTryCastFailure(Sequence[int], [True])
        self.assertTryCastFailure(Sequence[int], [1, True])

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

        # MutableSequence[T]-like lists
        self.assertTryCastFailure(MutableSequence[int], [True])
        self.assertTryCastFailure(MutableSequence[int], [1, True])

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

            # dict[K, V]-like dicts
            self.assertTryCastFailure(dict[str, int], {"x": True})
            self.assertTryCastFailure(dict[str, int], {"x": 1, "y": True})

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

        # dict[K, V]-like dicts
        self.assertTryCastFailure(Dict[str, int], {"x": True})
        self.assertTryCastFailure(Dict[str, int], {"x": 1, "y": True})

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

        # Mapping[K, V]-like dicts
        self.assertTryCastFailure(Mapping[str, int], {"x": True})
        self.assertTryCastFailure(Mapping[str, int], {"x": 1, "y": True})

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

        # MutableMapping[K, V]-like dicts
        self.assertTryCastFailure(MutableMapping[str, int], {"x": True})
        self.assertTryCastFailure(MutableMapping[str, int], {"x": 1, "y": True})

        # non-MutableMapping[K, V]s
        self.assertTryCastFailure(MutableMapping[str, int], 0)
        self.assertTryCastFailure(MutableMapping[str, int], "foo")
        self.assertTryCastFailure(MutableMapping[str, int], [1])
        self.assertTryCastFailure(MutableMapping[str, int], {1: 1})
        self.assertTryCastFailure(MutableMapping[str, int], {1})
        self.assertTryCastFailure(MutableMapping[str, int], object())

    # === TypedDicts ===

    def test_typeddict(self) -> None:
        class Point2D(TypedDict):
            x: int
            y: int

        class PartialPoint2D(TypedDict, total=False):
            x: int
            y: int

        class Point3D(TypedDict):
            x: int
            y: int
            z: int

        # Point2D
        self.assertTryCastSuccess(Point2D, {"x": 1, "y": 1})
        self.assertTryCastFailure(Point2D, {"x": 1, "y": 1, "z": 1})

        # PartialPoint2D
        self.assertTryCastSuccess(PartialPoint2D, {"x": 1, "y": 1})
        self.assertTryCastSuccess(PartialPoint2D, {"y": 1})
        self.assertTryCastSuccess(PartialPoint2D, {"x": 1})
        self.assertTryCastSuccess(PartialPoint2D, {})
        self.assertTryCastFailure(PartialPoint2D, {"x": 1, "y": 1, "z": 1})

        # Point3D
        self.assertTryCastFailure(Point3D, {"x": 1, "y": 1})
        self.assertTryCastSuccess(Point3D, {"x": 1, "y": 1, "z": 1})

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
                _MaybeBookBasedMovie,
                dict(
                    based_on="Blade Runner",
                ),
            )
        else:
            self.assertTryCastFailure(
                _MaybeBookBasedMovie,
                dict(
                    based_on="Blade Runner",
                ),
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
                _BookBasedMaybeMovie,
                dict(
                    based_on="Blade Runner",
                ),
            )
        else:
            _4 = _BookBasedMaybeMovie(
                based_on="Blade Runner",
            )
            self.assertTryCastSuccess(
                _BookBasedMaybeMovie,
                dict(
                    based_on="Blade Runner",
                ),
            )

    def test_typeddict_multiple_inheritance(self) -> None:
        _1 = XYZ(
            x=1,
            y="2",
            z=True,
        )
        self.assertTryCastSuccess(
            XYZ,
            dict(
                x=1,
                y="2",
                z=True,
            ),
        )

        self.assertTryCastFailure(
            XYZ,
            dict(
                y="2",
                z=True,
            ),
        )
        self.assertTryCastFailure(
            XYZ,
            dict(
                x=1,
                z=True,
            ),
        )
        self.assertTryCastFailure(
            XYZ,
            dict(
                x=1,
                y="2",
            ),
        )

    def test_typeddict_required_notrequired(self) -> None:
        import typing_extensions

        if not hasattr(typing_extensions, "get_type_hints"):
            self.skipTest("Checking for Required and NotRequired requires Python 3.7+")

        class TotalMovie(typing_extensions.TypedDict):
            title: str
            year: typing_extensions.NotRequired[int]

        class NontotalMovie(typing_extensions.TypedDict, total=False):
            title: typing_extensions.Required[str]
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

    def test_typeddict_using_mapping_value(self) -> None:
        class NamedObject(TypedDict):
            name: str

        class ValuedObject(TypedDict):
            value: object

        class MyNamedMapping(Mapping):
            def __init__(self, name: str) -> None:
                self._name = name

            def __getitem__(self, key: str) -> object:
                if key == "name":
                    return self._name
                else:
                    raise AttributeError

            def __len__(self) -> int:
                return 1

            def __iter__(self):
                return (x for x in ["name"])

        self.assertTryCastSuccess(NamedObject, MyNamedMapping("Isabelle"))
        self.assertTryCastFailure(ValuedObject, MyNamedMapping("Isabelle"))

    # === Tuples (Heterogeneous) ===

    if sys.version_info >= (3, 9):
        # TODO: Upgrade mypy to a version that supports PEP 585 and `tuple[Ts]`
        if not TYPE_CHECKING:

            def test_tuple_ts(self) -> None:
                # tuple[Ts]
                self.assertTryCastSuccess(tuple[int], (1,))
                self.assertTryCastSuccess(tuple[int, str], (1, "a"))
                self.assertTryCastSuccess(tuple[int, str, bool], (1, "a", True))

                # tuple[Ts]-like tuples
                self.assertTryCastFailure(tuple[int], ("A",))
                self.assertTryCastFailure(tuple[int, str], (1, 2))
                self.assertTryCastFailure(tuple[int, str, bool], (1, "a", object()))

                # tuple[Ts]-like lists
                self.assertTryCastFailure(tuple[int], [1])
                self.assertTryCastFailure(tuple[int, str], [1, "a"])
                self.assertTryCastFailure(tuple[int, str, bool], [1, "a", True])

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

    # === Special Types: Any, NoReturn ===

    def test_any(self) -> None:
        self.assertTryCastSuccess(Any, "words")
        self.assertTryCastSuccess(Any, 1)
        self.assertTryCastSuccess(Any, None)
        self.assertTryCastSuccess(Any, str)

    def test_noreturn(self) -> None:
        self.assertTryCastFailure(NoReturn, "words")
        self.assertTryCastFailure(NoReturn, 1)
        self.assertTryCastFailure(NoReturn, None)
        self.assertTryCastFailure(NoReturn, str)

        self.assertTryCastFailure(NoReturn, ValueError)
        self.assertTryCastFailure(NoReturn, ValueError())

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

    if sys.version_info >= (3, 7):

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

        class Point3D(Point2D, total=False):
            z: int

        try:
            trycast(Point3D, {"x": 1, "y": 2}, strict=True)
        except TypeNotSupportedError:
            pass
        else:
            self.fail("Expected TypeNotSupportedError to be raised")

    # NOTE: Cannot combine the following two if-checks with an `and`
    #       because that is too complicated for Pyre to understand.
    #
    #       For more info about the forms that Pyre supports, see its tests:
    #       https://github.com/facebook/pyre-check/blob/ee6d16129c112fb1feb1435a245d5e6a114e58d9/analysis/test/preprocessingTest.ml#L626
    if sys.version_info >= (3, 8):
        if sys.version_info < (3, 9):

            def test_rejects_python_3_8_typeddict_when_strict_is_true(self) -> None:
                class Point2D(typing.TypedDict):
                    x: int
                    y: int

                class Point3D(Point2D, total=False):
                    z: int

                try:
                    trycast(Point3D, {"x": 1, "y": 2}, strict=True)
                except TypeNotSupportedError:
                    pass
                else:
                    self.fail("Expected TypeNotSupportedError to be raised")

    # === Misuse: Nice Error Messages ===

    def test_tuple_of_types(self) -> None:
        self.assertRaisesRegex(
            TypeError,
            "does not support checking against a tuple of types",
            lambda: trycast((int, str), 1),  # type: ignore
        )

    def test_reversing_order_of_first_two_arguments_gives_nice_error_message(
        self,
    ) -> None:
        self.assertEqual(1, trycast(int, 1))

        self.assertRaisesRegex(
            TypeError,
            "requires a type as its first argument",
            lambda: trycast(1, int),
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
                    raise AssertionError(
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

    # === Typecheck ===

    def test_no_mypy_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["mypy"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            self.fail(
                f'mypy typechecking failed:\n\n{e.output.decode("utf-8").strip()}'
            )

    # TODO: This test runs very slowly (4.8 seconds on @davidfstr's laptop).
    #       Investigate way to configure pyright to have a faster startup time.
    def test_no_pyright_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["pyright"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            self.fail(
                f'pyright typechecking failed:\n\n{e.output.decode("utf-8").strip()}'
            )

    def test_no_pyre_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["pyre", "check"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
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

    # === Utility ===

    def assertTryCastSuccess(self, tp: object, value: object) -> None:
        self.assertIs(value, trycast(tp, value))

    def assertTryCastFailure(self, tp: object, value: object) -> None:
        self.assertIs(None, trycast(tp, value))

    def assertTryCastNoneSuccess(self, tp: object) -> None:
        self.assertIs(None, trycast(tp, None, _FAILURE))


class _TypingExtensionsGoneLoader(MetaPathFinder):
    def find_spec(self, module_name, parent_path, old_module_object=None):
        if module_name == "typing_extensions" and parent_path is None:
            raise ModuleNotFoundError
        return None


from trycast import _is_typed_dict

if sys.version_info >= (3, 8):
    from typing import TypedDict as TypingTypedDict

    class TypingPoint(TypingTypedDict):
        x: int
        y: int


from typing_extensions import TypedDict as TypingExtensionsTypedDict


class TypingExtensionsPoint(TypingExtensionsTypedDict):
    x: int
    y: int


from mypy_extensions import TypedDict as MypyExtensionsTypedDict


class MypyExtensionsPoint(MypyExtensionsTypedDict):  # type: ignore[reportGeneralTypeIssues]  # pyright
    x: int
    y: int


class TestIsTypedDict(TestCase):
    if sys.version_info >= (3, 8):

        def test_recognizes_typed_dict_from_typing(self) -> None:
            self.assertTrue(_is_typed_dict(TypingPoint))

    def test_recognizes_typed_dict_from_typing_extensions(self) -> None:
        self.assertTrue(_is_typed_dict(TypingExtensionsPoint))

    def test_recognizes_typed_dict_from_mypy_extensions(self) -> None:
        self.assertTrue(_is_typed_dict(MypyExtensionsPoint))


class _Cell(TypedDict):
    value: object


class TestIsAssignable(TestCase):
    def test_is_similar_to_isinstance(self) -> None:
        self.assertTrue(isassignable("words", str))
        self.assertTrue(isassignable(1, int))
        self.assertTrue(isassignable(True, bool))

        self.assertFalse(isassignable("words", int))
        self.assertFalse(isassignable(1, str))
        self.assertFalse(isassignable(True, str))

    def test_is_different_from_isinstance_where_pep_484_differs(self) -> None:
        self.assertFalse(isassignable(True, int))

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

    @staticmethod
    def _demands_a_typeddict(cell: _Cell) -> object:
        return cell["value"]

    # TODO: Add support for this case if/when support for a "strict" TypeGuard
    #       of some kind is introduced that narrows in the negative case.
    # def test_return_type_is_typeguarded_negatively(self) -> None:
    #    value = 'words'
    #    if not isassignable(value, str):
    #        self._demands_a_never(value)  # ensure typechecks

    @staticmethod
    def _demands_a_never(value: NoReturn) -> NoReturn:
        raise ValueError("expected this code to be unreachable")
