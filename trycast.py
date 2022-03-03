import sys
from collections.abc import Mapping as CMapping
from collections.abc import MutableMapping as CMutableMapping
from collections.abc import MutableSequence as CMutableSequence
from collections.abc import Sequence as CSequence
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

try:
    # Python 3.7+
    from typing_extensions import get_type_hints  # type: ignore[attr-defined]
except ImportError:
    # Python 3.6
    from typing import get_type_hints  # type: ignore[misc]  # incompatible import

# Literal
if sys.version_info >= (3, 8):
    from typing import Literal  # Python 3.8+
else:
    try:
        from typing_extensions import Literal  # Python 3.5+
    except ImportError:
        if not TYPE_CHECKING:

            class Literal:
                pass


# get_origin, get_args
if sys.version_info >= (3, 8):
    from typing import get_args, get_origin  # Python 3.8+

elif sys.version_info >= (3, 7):
    from typing import _GenericAlias  # type: ignore  # private API not in stubs

    def get_origin(tp: object) -> Optional[object]:
        if isinstance(tp, _GenericAlias):
            return tp.__origin__  # type: ignore  # private API not in stubs
        else:
            return None

    def get_args(tp: object) -> Tuple[object, ...]:
        if isinstance(tp, _GenericAlias):
            return tp.__args__  # type: ignore  # private API not in stubs
        else:
            return ()

elif sys.version_info >= (3, 6):
    from typing import GenericMeta  # type: ignore  # private API not in stubs
    from typing import _Union  # type: ignore  # private API not in stubs

    try:
        from typing_extensions import (  # type: ignore  # private API not in stubs
            _Literal,
        )
    except ImportError:
        if not TYPE_CHECKING:

            class _Literal:
                pass

    def get_origin(tp: object) -> Optional[object]:
        if isinstance(tp, GenericMeta):
            return tp.__origin__  # type: ignore  # private API not in stubs
        elif isinstance(tp, _Union):
            return Union
        elif isinstance(tp, _Literal):
            return Literal
        else:
            return None

    def get_args(tp: object) -> Tuple[object, ...]:
        if isinstance(tp, GenericMeta):
            return tp.__args__  # type: ignore  # private API not in stubs
        elif isinstance(tp, _Union):
            return tp.__args__
        elif isinstance(tp, _Literal):
            return tp.__values__
        else:
            return ()

else:
    raise ImportError("Expected Python 3.6 or later.")


# _is_typed_dict
_typed_dict_meta_list = []
try:
    # private API not in stubs.
    from typing import _TypedDictMeta as _TypingTypedDictMeta  # type: ignore

    _typed_dict_meta_list.append(_TypingTypedDictMeta)
except ImportError:
    pass

try:
    from typing_extensions import (  # type: ignore # isort: skip
        _TypedDictMeta as _TypingExtensionsTypedDictMeta,
    )

    _typed_dict_meta_list.append(_TypingExtensionsTypedDictMeta)
except ImportError:
    pass


try:
    from mypy_extensions import (  # type: ignore # isort: skip
        _TypedDictMeta as _MypyExtensionsTypedDictMeta,
    )

    _typed_dict_meta_list.append(_MypyExtensionsTypedDictMeta)
except ImportError:
    pass

_typed_dict_metas = tuple(_typed_dict_meta_list)


def _is_typed_dict(tp: object) -> bool:
    return isinstance(tp, _typed_dict_metas)


__all__ = ("trycast",)


_T = TypeVar("_T")
_F = TypeVar("_F")
_SimpleTypeVar = TypeVar("_SimpleTypeVar")
_SimpleTypeVarCo = TypeVar("_SimpleTypeVarCo", covariant=True)

_MISSING = object()
_FAILURE = object()

if TYPE_CHECKING:
    from typing_extensions import TypeAlias, TypeGuard

    TypeGuard_T: TypeAlias = TypeGuard[_T]
else:
    TypeGuard_T = bool


# TODO: Use this signature for trycast once support for TypeForm is
#       implemented in mypy.
# @overload
# def trycast(tp: TypeForm[_T], value: object) -> Optional[_T]: ...
# @overload
# def trycast(tp: TypeForm[_T], value: object, failure: _F) -> Union[_T, _F]: ...


@overload
def trycast(tp: object, value: object, *, strict: bool = False) -> Optional[object]:
    ...


@overload
def trycast(
    tp: object, value: object, failure: _F, *, strict: bool = False
) -> Union[object, _F]:
    ...


def trycast(tp, value, failure=None, *, strict=False):
    """
    If `value` is in the shape of `tp` (as accepted by a Python typechecker
    conforming to PEP 484 "Type Hints") then returns it, otherwise returns
    `failure` (which is None by default).

    This method logically performs an operation similar to:

        return value if isinstance(tp, value) else failure

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

    If strict=False then trycast will additionally accept
    mypy_extensions.TypedDict instances and Python 3.8 typing.TypedDict
    instances for the `tp` parameter. Normally these kinds of types are
    rejected by trycast with a TypeNotSupportedError because these
    types do not preserve enough information at runtime to reliably
    determine which keys are required and which are potentially-missing.

    Raises:
    * TypeNotSupportedError --
        If strict=True and either mypy_extensions.TypedDict or a
        Python 3.8 typing.TypedDict is found within the `tp` argument.
    """
    if tp is int:
        # Do not accept bools as valid int values
        if isinstance(value, int) and not isinstance(value, bool):
            return cast(_T, value)
        else:
            return failure

    if tp is float:
        # 1. Accept ints as valid float values
        # 2. Do not accept bools as valid float values
        if isinstance(value, float) or (
            isinstance(value, int) and not isinstance(value, bool)
        ):
            return cast(_T, value)
        else:
            return failure

    type_origin = get_origin(tp)
    if type_origin is list or type_origin is List:  # List, List[T]
        return _trycast_listlike(tp, value, failure, list)

    if type_origin is tuple or type_origin is Tuple:
        if isinstance(value, tuple):
            type_args = get_args(tp)

            if len(type_args) == 0 or (
                len(type_args) == 2 and type_args[1] is Ellipsis
            ):  # Tuple, Tuple[T, ...]

                return _trycast_listlike(
                    tp,
                    value,
                    failure,
                    tuple,
                    covariant_t=True,
                    t_ellipsis=True,
                )
            else:  # Tuple[Ts]
                if len(value) != len(type_args):
                    return failure

                for (T, t) in zip(type_args, value):
                    if trycast(T, t, _FAILURE) is _FAILURE:
                        return failure

                return cast(_T, value)
        else:
            return failure

    if type_origin is Sequence or type_origin is CSequence:  # Sequence, Sequence[T]
        return _trycast_listlike(tp, value, failure, CSequence, covariant_t=True)

    if (
        type_origin is MutableSequence or type_origin is CMutableSequence
    ):  # MutableSequence, MutableSequence[T]
        return _trycast_listlike(tp, value, failure, CMutableSequence)

    if type_origin is dict or type_origin is Dict:  # Dict, Dict[K, V]
        return _trycast_dictlike(tp, value, failure, dict)

    if type_origin is Mapping or type_origin is CMapping:  # Mapping, Mapping[K, V]
        return _trycast_dictlike(tp, value, failure, CMapping, covariant_v=True)

    if (
        type_origin is MutableMapping or type_origin is CMutableMapping
    ):  # MutableMapping, MutableMapping[K, V]
        return _trycast_dictlike(tp, value, failure, CMutableMapping)

    if type_origin is Union:  # Union[T1, T2, ...]
        for T in get_args(tp):
            if trycast(T, value, _FAILURE) is not _FAILURE:
                return cast(_T, value)
        return failure

    if type_origin is Literal:  # Literal[...]
        for literal in get_args(tp):
            if value == literal:
                return cast(_T, value)
        return failure

    if _is_typed_dict(tp):  # T extends TypedDict
        if isinstance(value, Mapping):
            resolved_annotations = get_type_hints(
                tp
            )  # resolve ForwardRefs in tp.__annotations__

            try:
                # {typing in Python 3.9+, typing_extensions}.TypedDict
                required_keys = tp.__required_keys__
            except AttributeError:
                # {typing in Python 3.8, mypy_extensions}.TypedDict
                if strict:
                    if sys.version_info[:2] >= (3, 9):
                        advise = "Suggest use a typing.TypedDict instead."
                    else:
                        advise = "Suggest use a typing_extensions.TypedDict instead."
                    raise TypeNotSupportedError(
                        "trycast cannot determine which keys are required "
                        "and which are potentially-missing for the "
                        "specified kind of TypedDict. " + advise
                    )
                else:
                    if tp.__total__:
                        required_keys = resolved_annotations.keys()
                    else:
                        required_keys = frozenset()

            for (k, v) in value.items():
                V = resolved_annotations.get(k, _MISSING)
                if V is _MISSING or trycast(V, v, _FAILURE) is _FAILURE:
                    return failure

            for k in required_keys:
                if k not in value:
                    return failure
            return cast(_T, value)
        else:
            return failure

    if isinstance(tp, tuple):
        raise TypeError(
            "trycast does not support checking against a tuple of types. "
            "Try checking against a Union[T1, T2, ...] instead."
        )

    if isinstance(value, tp):  # type: ignore
        return value
    else:
        return failure


class TypeNotSupportedError(ValueError):
    pass


def _trycast_listlike(
    tp, value, failure, listlike_type, *, covariant_t=False, t_ellipsis=False
):
    if isinstance(value, listlike_type):
        T_ = get_args(tp)

        if len(T_) == 0:  # Python 3.9+
            (T,) = (_SimpleTypeVarCo if covariant_t else _SimpleTypeVar,)

        else:
            if t_ellipsis:
                if len(T_) == 2 and T_[1] is Ellipsis:
                    (T, _) = T_
                else:
                    return failure
            else:
                (T,) = T_

        if _is_simple_typevar(T, covariant=covariant_t):
            pass
        else:
            for x in value:
                if trycast(T, x, _FAILURE) is _FAILURE:
                    return failure

        return cast(_T, value)
    else:
        return failure


def _trycast_dictlike(tp, value, failure, dictlike_type, *, covariant_v=False):
    if isinstance(value, dictlike_type):
        K_V = get_args(tp)

        if len(K_V) == 0:  # Python 3.9+
            (K, V) = (
                _SimpleTypeVar,
                _SimpleTypeVarCo if covariant_v else _SimpleTypeVar,
            )
        else:
            (K, V) = K_V

        if _is_simple_typevar(K) and _is_simple_typevar(V, covariant=covariant_v):
            pass
        else:
            for (k, v) in value.items():
                if (
                    trycast(K, k, _FAILURE) is _FAILURE
                    or trycast(V, v, _FAILURE) is _FAILURE
                ):
                    return failure
        return cast(_T, value)
    else:
        return failure


def _is_simple_typevar(T: object, covariant: bool = False) -> bool:
    return (
        isinstance(T, TypeVar)
        and T.__constraints__ == ()
        and T.__covariant__ == covariant
        and T.__contravariant__ is False
        and T.__constraints__ == ()
    )


# TODO: Use this signature for isassignable once support for TypeForm is
#       implemented in mypy. See: https://github.com/python/mypy/issues/9773
# @overload
# def isassignable(value: object, tp: TypeForm[_T]) -> TypeGuard_T: ...


@overload
def isassignable(value: object, tp: Type[_T]) -> TypeGuard_T:
    ...


@overload
def isassignable(value: object, tp: object) -> bool:
    ...


def isassignable(value, tp):
    """
    Returns whether `value` is in the shape of `tp`
    (as accepted by a Python typechecker conforming to PEP 484 "Type Hints").

    This method logically performs an operation similar to:

        return isinstance(tp, value)

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
    """
    if trycast(tp, value, _isassignable_failure, strict=True) is _isassignable_failure:
        return False
    else:
        return True


_isassignable_failure = object()
