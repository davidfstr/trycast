# flake8: noqa
import os
import subprocess
import sys
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)
from unittest import TestCase

import test_data.forwardrefs_example
from tests_shape_example import HTTP_400_BAD_REQUEST, draw_shape_endpoint, shapes_drawn
from trycast import trycast

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
        self.assertRaises(TypeError, lambda: trycast(None, None))  # type: ignore

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
        # TODO: Upgrade mypy to a version that supports PEP 585 and `list[int]`
        if not TYPE_CHECKING:

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
        # TODO: Upgrade mypy to a version that supports PEP 585 and `tuple[int, ...]`
        if not TYPE_CHECKING:

            def test_tuple_t_ellipsis(self) -> None:
                # Actual tuple[T, ...]
                self.assertTryCastSuccess(tuple[int, ...], ())
                self.assertTryCastSuccess(tuple[int, ...], (1,))
                self.assertTryCastSuccess(tuple[int, ...], (1, 2))

                # tuple[T, ...]-like tuples
                self.assertTryCastFailure(tuple[int, ...], (True,))
                self.assertTryCastFailure(tuple[int, ...], (1, True))

                # non-tuple[T, ...]s
                self.assertTryCastFailure(tuple[int, ...], 0)
                self.assertTryCastFailure(tuple[int, ...], "foo")
                self.assertTryCastFailure(tuple[int, ...], ["1"])
                self.assertTryCastFailure(tuple[int, ...], {1: 1})
                self.assertTryCastFailure(tuple[int, ...], {1})
                self.assertTryCastFailure(tuple[int, ...], object())

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
        # TODO: Upgrade mypy to a version that supports PEP 585 and `dict[str, int]`
        if not TYPE_CHECKING:

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
        class Movie(TypedDict):
            name: str
            year: int

        class BookBasedMovie(Movie):
            based_on: str

        _1: BookBasedMovie = dict(
            name="Blade Runner",
            year=1982,
            based_on="Blade Runner",
        )
        self.assertTryCastSuccess(
            BookBasedMovie,
            dict(
                name="Blade Runner",
                year=1982,
                based_on="Blade Runner",
            ),
        )

        self.assertTryCastFailure(
            BookBasedMovie,
            dict(
                name="Blade Runner",
                year=1982,
            ),
        )
        self.assertTryCastFailure(
            BookBasedMovie,
            dict(
                based_on="Blade Runner",
            ),
        )

    def test_typeddict_single_inheritance_with_mixed_totality(self) -> None:
        class Movie(TypedDict):
            name: str
            year: int

        class MaybeBookBasedMovie(Movie, total=False):
            based_on: str

        _1: MaybeBookBasedMovie = dict(
            name="Blade Runner",
            year=1982,
            based_on="Blade Runner",
        )
        self.assertTryCastSuccess(
            MaybeBookBasedMovie,
            dict(
                name="Blade Runner",
                year=1982,
                based_on="Blade Runner",
            ),
        )

        _2: MaybeBookBasedMovie = dict(
            name="Blade Runner",
            year=1982,
        )
        self.assertTryCastSuccess(
            MaybeBookBasedMovie,
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
                MaybeBookBasedMovie,
                dict(
                    based_on="Blade Runner",
                ),
            )
        else:
            self.assertTryCastFailure(
                MaybeBookBasedMovie,
                dict(
                    based_on="Blade Runner",
                ),
            )

        class MaybeMovie(TypedDict, total=False):
            name: str
            year: int

        class BookBasedMaybeMovie(MaybeMovie):
            based_on: str

        _3: BookBasedMaybeMovie = dict(
            name="Blade Runner",
            year=1982,
            based_on="Blade Runner",
        )
        self.assertTryCastSuccess(
            BookBasedMaybeMovie,
            dict(
                name="Blade Runner",
                year=1982,
                based_on="Blade Runner",
            ),
        )

        self.assertTryCastFailure(
            BookBasedMaybeMovie,
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
                BookBasedMaybeMovie,
                dict(
                    based_on="Blade Runner",
                ),
            )
        else:
            _4: BookBasedMaybeMovie = dict(
                based_on="Blade Runner",
            )
            self.assertTryCastSuccess(
                BookBasedMaybeMovie,
                dict(
                    based_on="Blade Runner",
                ),
            )

    def test_typeddict_multiple_inheritance(self) -> None:
        class X(TypedDict):
            x: int

        class Y(TypedDict):
            y: str

        class XYZ(X, Y):
            z: bool

        _1: XYZ = dict(
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

    # === Forward References ===

    def test_typeddict_with_forwardrefs(self) -> None:
        self.assertTryCastSuccess(
            test_data.forwardrefs_example.Circle,
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

    def test_alias_to_union_with_forwardrefs(self) -> None:
        # Union with forward refs
        # TODO: Find way to auto-resolve forward references
        #       inside Union types.
        self.assertRaises(
            # TODO: Check the error message. Make it reasonable,
            #       explaining the forward references could not be resolved.
            TypeError,
            lambda: trycast(
                test_data.forwardrefs_example.Shape,
                dict(type="circle", center=dict(x=50, y=50), radius=25),
            ),
        )

        # Union with forward refs that have been resolved
        self.assertTryCastSuccess(
            eval_type(
                test_data.forwardrefs_example.Shape,
                test_data.forwardrefs_example.__dict__,
                None,
            ),
            dict(type="circle", center=dict(x=50, y=50), radius=25),
        )

    def test_alias_to_list_with_forwardrefs(self) -> None:
        # list with forward refs
        # TODO: Find way to auto-resolve forward references
        #       inside collection types.
        self.assertRaises(
            # TODO: Check the error message. Make it reasonable,
            #       explaining the forward references could not be resolved.
            TypeError,
            lambda: trycast(
                test_data.forwardrefs_example.Scatterplot, [dict(x=50, y=50)]
            ),
        )

        # list with forward refs that have been resolved
        self.assertTryCastSuccess(
            eval_type(
                test_data.forwardrefs_example.Scatterplot,
                test_data.forwardrefs_example.__dict__,
                None,
            ),
            [dict(x=50, y=50)],
        )

    def test_alias_to_dict_with_forwardrefs(self) -> None:
        # dict with forward refs
        # TODO: Find way to auto-resolve forward references
        #       inside collection types.
        self.assertRaises(
            # TODO: Check the error message. Make it reasonable,
            #       explaining the forward references could not be resolved.
            TypeError,
            lambda: trycast(
                test_data.forwardrefs_example.PointForLabel,
                {"Target": dict(x=50, y=50)},
            ),
        )

        # dict with forward refs that have been resolved
        self.assertTryCastSuccess(
            eval_type(
                test_data.forwardrefs_example.PointForLabel,
                test_data.forwardrefs_example.__dict__,
                None,
            ),
            {"Target": dict(x=50, y=50)},
        )

    # === Special ===

    def test_tuple_of_types(self) -> None:
        self.assertRaises(TypeError, lambda: trycast((int, str), 1))  # type: ignore

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

    def test_no_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ["mypy"],
                env={"LANG": "en_US.UTF-8", "PATH": os.environ.get("PATH", "")},
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            self.fail(f'Typechecking failed:\n\n{e.output.decode("utf-8").strip()}')

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


class MypyExtensionsPoint(MypyExtensionsTypedDict):
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
