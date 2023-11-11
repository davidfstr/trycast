import builtins
import functools
import importlib
import inspect
import math
import re
import sys
from collections.abc import Callable as CCallable
from collections.abc import Mapping as CMapping
from collections.abc import MutableMapping as CMutableMapping
from collections.abc import MutableSequence as CMutableSequence
from collections.abc import Sequence as CSequence
from inspect import Parameter
from types import ModuleType
from typing import ForwardRef  # type: ignore[import-error]  # pytype (for ForwardRef)
from typing import _GenericAlias  # type: ignore[attr-defined]
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    NamedTuple,
    NewType,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from typing import _eval_type as eval_type  # type: ignore[attr-defined]
from typing import _type_repr as type_repr  # type: ignore[attr-defined]
from typing import cast, overload

try:
    from types import UnionType  # type: ignore[attr-defined]
except ImportError:

    class UnionType(type):  # type: ignore[no-redef]
        ...


# get_type_hints
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
                def __class_getitem__(cls, key):
                    pass


# TypeGuard
if sys.version_info >= (3, 10):
    from typing import TypeGuard  # Python 3.10+
else:
    try:
        from typing_extensions import (
            TypeGuard,  # type: ignore[not-supported-yet]  # pytype
        )
    except ImportError:
        if not TYPE_CHECKING:

            class TypeGuard:
                def __class_getitem__(cls, key):
                    return bool


# get_origin, get_args
if sys.version_info >= (3, 8):
    from typing import get_args, get_origin  # Python 3.8+

elif sys.version_info >= (3, 7):

    def get_origin(tp: object) -> Optional[object]:
        if isinstance(tp, _GenericAlias):  # type: ignore[16]  # pyre
            return tp.__origin__  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return None

    def get_args(tp: object) -> Tuple[object, ...]:
        if isinstance(tp, _GenericAlias):  # type: ignore[16]  # pyre
            return tp.__args__  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return ()

else:  # pragma: no cover
    raise ImportError("Expected Python 3.7 or later.")


# _is_typed_dict
_typed_dict_meta_list = []
try:
    from typing import (  # type: ignore[attr-defined]  # isort: skip
        _TypedDictMeta as _TypingTypedDictMeta,  # type: ignore[reportGeneralTypeIssues]  # pyright
    )

    _typed_dict_meta_list.append(_TypingTypedDictMeta)  # type: ignore[16]  # pyre
except ImportError:
    pass

try:
    from typing_extensions import (  # type: ignore[attr-defined]  # isort: skip
        _TypedDictMeta as _TypingExtensionsTypedDictMeta,  # type: ignore[reportGeneralTypeIssues]  # pyright
    )

    _typed_dict_meta_list.append(_TypingExtensionsTypedDictMeta)  # type: ignore[16]  # pyre
except ImportError:
    pass

try:
    from mypy_extensions import (  # type: ignore[attr-defined]  # isort: skip
        _TypedDictMeta as _MypyExtensionsTypedDictMeta,  # type: ignore[reportGeneralTypeIssues]  # pyright
    )

    _typed_dict_meta_list.append(_MypyExtensionsTypedDictMeta)  # type: ignore[16]  # pyre
except ImportError:
    pass

_typed_dict_metas = tuple(_typed_dict_meta_list)


def _is_typed_dict(tp: object) -> bool:
    return isinstance(tp, _typed_dict_metas)


# _is_newtype
if NewType.__class__.__name__ == "function":  # type: ignore[reportGeneralTypeIssues]  # pyright
    # Python 3.7 - 3.9
    def _is_newtype(tp: object) -> bool:
        return (
            hasattr(tp, "__class__")
            and tp.__class__.__name__ == "function"
            and hasattr(tp, "__qualname__")
            and tp.__qualname__.startswith("NewType.<locals>")  # type: ignore[attr-defined]
            and hasattr(tp, "__module__")
            and tp.__module__ == "typing"
        )

elif NewType.__class__.__name__ == "type":  # type: ignore[reportGeneralTypeIssues]  # pyright
    # Python 3.10+
    def _is_newtype(tp: object) -> bool:
        return isinstance(tp, NewType)  # type: ignore[arg-type]

else:
    raise AssertionError(
        "Do not know how to recognize NewType in this version of Python"
    )


# _inspect_signature
if sys.version_info >= (3, 10):

    def _inspect_signature(value):
        return inspect.signature(
            value,
            # Don't auto-unwrap decorated functions
            follow_wrapped=False,
            # Don't need annotation information
            eval_str=False,
        )

else:

    def _inspect_signature(value):
        return inspect.signature(
            value,
            # Don't auto-unwrap decorated functions
            follow_wrapped=False,
        )


# _type_check
if sys.version_info >= (3, 11):
    import types
    from typing import _GenericAlias  # type: ignore[attr-defined]  # noqa: F811
    from typing import (  # type: ignore[attr-defined]
        ClassVar,
        Final,
        Generic,
        ParamSpec,
        Protocol,
        _SpecialForm,
    )

    # Workaround https://github.com/python/cpython/issues/92601
    # by using Python 3.10's typing._type_check()
    def _type_check(arg: object, msg: str):
        """Check that the argument is a type, and return it (internal helper).

        As a special case, accept None and return type(None) instead. Also wrap strings
        into ForwardRef instances. Consider several corner cases, for example plain
        special forms like Union are not valid, while Union[int, str] is OK, etc.
        The msg argument is a human-readable error message, e.g::

            "Union[arg, ...]: arg should be a type."

        We append the repr() of the actual value (truncated to 100 chars).
        """
        is_argument = True
        module = None
        is_class = False

        invalid_generic_forms = (Generic, Protocol)  # type: tuple[object, ...]
        if not is_class:
            invalid_generic_forms += (ClassVar,)
            if is_argument:
                invalid_generic_forms += (Final,)

        arg = _type_convert(arg, module=module)
        if isinstance(arg, _GenericAlias) and arg.__origin__ in invalid_generic_forms:  # type: ignore[reportGeneralTypeIssues]  # pyright
            raise TypeError(f"{arg} is not valid as type argument")
        if arg in (Any, NoReturn, Final):
            return arg
        if isinstance(arg, _SpecialForm) or arg in (Generic, Protocol):
            raise TypeError(f"Plain {arg} is not valid as type argument")
        if isinstance(arg, (type, TypeVar, ForwardRef, types.UnionType, ParamSpec)):
            return arg
        if not callable(arg):
            raise TypeError(f"{msg} Got {arg!r:.100}.")
        return arg

    # Python 3.10's typing._type_convert()
    def _type_convert(arg, module=None):
        """For converting None to type(None), and strings to ForwardRef."""
        if arg is None:
            return type(None)
        if isinstance(arg, str):
            return ForwardRef(arg, module=module)
        return arg

else:
    from typing import _type_check  # type: ignore[attr-defined]


__all__ = (
    "trycast",
    "isassignable",
    # NOTE: May be part of the API in the future
    # "eval_type_str",
)


_T = TypeVar("_T")
_F = TypeVar("_F")
_SimpleTypeVar = TypeVar("_SimpleTypeVar")
_SimpleTypeVarCo = TypeVar("_SimpleTypeVarCo", covariant=True)  # type: ignore[not-supported-yet]  # pytest

_MISSING = object()
_FAILURE = object()

# ------------------------------------------------------------------------------
# trycast

# TODO: Once support for TypeForm is implemented in mypy,
#       replace the   `(Type[T]) -> Optional[T]` overload
#       and the       `(object) -> Optional[object]` overload with
#       the following `(TypeForm[T]) -> Optional[T]` overload:
#
#       See: https://github.com/python/mypy/issues/9773
# @overload
# def trycast(tp: TypeForm[_T], value: object) -> Optional[_T]: ...


@overload
def trycast(  # type: ignore[43]  # pyre
    tp: str, value: object, *, strict: bool = True, eval: Literal[False]
) -> NoReturn:
    ...  # pragma: no cover


@overload
def trycast(tp: str, value: object, *, strict: bool = True, eval: bool = True) -> bool:  # type: ignore[43]  # pyre
    ...  # pragma: no cover


@overload
def trycast(  # type: ignore[43]  # pyre
    tp: Type[_T], value: object, *, strict: bool = True, eval: bool = True
) -> Optional[_T]:
    ...  # pragma: no cover


@overload
def trycast(  # type: ignore[43]  # pyre
    tp: object, value: object, *, strict: bool = True, eval: bool = True
) -> Optional[object]:
    ...  # pragma: no cover


@overload
def trycast(
    tp: str,
    value: object,
    failure: object,
    *,
    strict: bool = True,
    eval: Literal[False],
) -> NoReturn:
    ...  # pragma: no cover


@overload
def trycast(
    tp: Type[_T], value: object, failure: _F, *, strict: bool = True, eval: bool = True
) -> Union[_T, _F]:
    ...  # pragma: no cover


@overload
def trycast(
    tp: object, value: object, failure: _F, *, strict: bool = True, eval: bool = True
) -> Union[object, _F]:
    ...  # pragma: no cover


def trycast(tp, value, failure=None, *, strict=True, eval=True):
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
    * strict --
        * If strict=False then trycast will additionally accept
          mypy_extensions.TypedDict instances and Python 3.8 typing.TypedDict
          instances for the `tp` parameter. Normally these kinds of types are
          rejected by trycast with a TypeNotSupportedError because these
          types do not preserve enough information at runtime to reliably
          determine which keys are required and which are potentially-missing.
        * If strict=False then trycast will treat `NewType("Foo", T)`
          the same as `T`. Normally NewTypes are rejected by trycast with a
          TypeNotSupportedError because values of NewTypes at runtime
          are indistinguishable from their wrapped supertype.
    * eval --
        If eval=False then trycast will not attempt to resolve string
        type references, which requires the use of the eval() function.
        Otherwise string type references will be accepted.

    Raises:
    * TypeNotSupportedError --
        * If strict=True and either mypy_extensions.TypedDict or a
          Python 3.8 typing.TypedDict is found within the `tp` argument.
        * If strict=True and a NewType is found within the `tp` argument.
        * If a TypeVar is found within the `tp` argument.
        * If an unrecognized Generic type is found within the `tp` argument.
    * UnresolvedForwardRefError --
        If `tp` is a type form which contains a ForwardRef.
    * UnresolvableTypeError --
        If `tp` is a string that could not be resolved to a type.
    """
    options = _TrycastOptions(strict, eval)
    if isinstance(tp, str):
        if eval:  # == options.eval (for pytype)
            tp = eval_type_str(tp)  # does use eval()
        else:
            raise UnresolvableTypeError(
                f"Could not resolve type {tp!r}: "
                f"Type appears to be a string reference "
                f"and trycast() was called with eval=False, "
                f"disabling eval of string type references."
            )
    else:
        try:
            tp = _type_check(tp, "trycast() requires a type as its first argument.")
        except TypeError:
            if isinstance(tp, tuple) and len(tp) >= 1 and isinstance(tp[0], type):
                raise TypeError(
                    "trycast does not support checking against a tuple of types. "
                    "Try checking against a Union[T1, T2, ...] instead."
                )
            else:
                raise
    try:
        return _trycast_inner(tp, value, failure, options)  # type: ignore[bad-return-type]  # pytype
    except UnresolvedForwardRefError:
        if options.eval:
            advise = (
                "Try altering the first type argument to be a string "
                "reference (surrounded with quotes) instead."
            )
        else:
            advise = (
                "trycast() cannot resolve string type references "
                "because it was called with eval=False."
            )
        raise UnresolvedForwardRefError(
            f"trycast does not support checking against type form {tp!r} "
            "which contains a string-based forward reference. "
            f"{advise}"
        )


class _TrycastOptions(NamedTuple):
    strict: bool
    eval: bool


# TODO: Use this signature for _trycast_inner once support for TypeForm is
#       implemented in mypy. See: https://github.com/python/mypy/issues/9773
# @overload
# def _trycast_inner(tp: TypeForm[_T], value: object, failure: _F) -> Union[_T, _F]: ...


@overload
def _trycast_inner(
    tp: Type[_T], value: object, failure: _F, options: _TrycastOptions
) -> Union[_T, _F]:
    ...  # pragma: no cover


@overload
def _trycast_inner(
    tp: object, value: object, failure: _F, options: _TrycastOptions
) -> Union[object, _F]:
    ...  # pragma: no cover


def _trycast_inner(tp, value, failure, options):
    """
    Raises:
    * TypeNotSupportedError
    * UnresolvedForwardRefError
    """
    if tp is int:
        # Also accept bools as valid int values
        if isinstance(value, int):
            return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return failure

    if tp is float:
        # Also accept ints and bools as valid float values
        if isinstance(value, float) or isinstance(value, int):
            return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return failure

    if tp is complex:
        # Also accept floats, ints, and bools as valid complex values
        if (
            isinstance(value, complex)
            or isinstance(value, float)
            or isinstance(value, int)
        ):
            return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return failure

    type_origin = get_origin(tp)

    if type_origin is list or type_origin is List:  # List, List[T]
        return _trycast_listlike(tp, value, failure, list, options)

    if type_origin is set or type_origin is Set:  # Set, Set[T]
        return _trycast_listlike(tp, value, failure, set, options)

    if type_origin is frozenset or type_origin is FrozenSet:  # FrozenSet, FrozenSet[T]
        return _trycast_listlike(
            tp, value, failure, frozenset, options, covariant_t=True
        )

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
                    options,
                    covariant_t=True,
                    t_ellipsis=True,
                )
            else:  # Tuple[Ts]
                if len(value) != len(type_args):
                    return failure

                for (T, t) in zip(type_args, value):
                    if _trycast_inner(T, t, _FAILURE, options) is _FAILURE:
                        return failure

                return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return failure

    if type_origin is Sequence or type_origin is CSequence:  # Sequence, Sequence[T]
        return _trycast_listlike(
            tp, value, failure, CSequence, options, covariant_t=True
        )

    if (
        type_origin is MutableSequence or type_origin is CMutableSequence
    ):  # MutableSequence, MutableSequence[T]
        return _trycast_listlike(tp, value, failure, CMutableSequence, options)

    if type_origin is dict or type_origin is Dict:  # Dict, Dict[K, V]
        return _trycast_dictlike(tp, value, failure, dict, options)

    if type_origin is Mapping or type_origin is CMapping:  # Mapping, Mapping[K, V]
        return _trycast_dictlike(
            tp, value, failure, CMapping, options, covariant_v=True
        )

    if (
        type_origin is MutableMapping or type_origin is CMutableMapping
    ):  # MutableMapping, MutableMapping[K, V]
        return _trycast_dictlike(tp, value, failure, CMutableMapping, options)

    if type_origin is Union or type_origin is UnionType:  # Union[T1, T2, ...]
        for T in get_args(tp):
            if _trycast_inner(T, value, _FAILURE, options) is not _FAILURE:  # type: ignore[wrong-arg-types]  # pytype
                if isinstance(tp, type):
                    return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
                else:
                    return value
        return failure

    if type_origin is Literal:  # Literal[...]
        for literal in get_args(tp):
            if value == literal:
                if isinstance(tp, type):
                    return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
                else:
                    return value
        return failure

    if type_origin is CCallable:
        callable_args = get_args(tp)
        if callable_args == ():
            # Callable
            if callable(value):
                return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
            else:
                return failure
        else:
            if len(callable_args) != 2 or (
                callable_args[0] is not Ellipsis
                and not isinstance(callable_args[0], list)
            ):
                # Python 3.7
                callable_args = (
                    list(callable_args[: len(callable_args) - 1]),
                    callable_args[len(callable_args) - 1],
                )

            assert len(callable_args) == 2
            (param_types, return_type) = callable_args

            if return_type is not Any:
                # Callable[..., T]
                raise TypeNotSupportedError(
                    f"trycast cannot reliably determine whether value is "
                    f"a {type_repr(tp)} because "
                    f"callables at runtime do not always have a "
                    f"declared return type. "
                    f"Consider using trycast(Callable, value) instead."
                )

            if param_types is Ellipsis:
                # Callable[..., Any]
                return _trycast_inner(Callable, value, failure, options)

            assert isinstance(param_types, list)
            for param_type in param_types:
                if param_type is not Any:
                    raise TypeNotSupportedError(
                        f"trycast cannot reliably determine whether value is "
                        f"a {type_repr(tp)} because "
                        f"callables at runtime do not always have "
                        f"declared parameter types. "
                        f"Consider using trycast("
                        f"Callable[{','.join('Any' * len(param_types))}, Any], value) "
                        f"instead."
                    )

            # Callable[[Any * N], Any]
            if callable(value):
                try:
                    sig = _inspect_signature(value)
                except TypeError:
                    # Not a callable
                    return failure
                except ValueError:
                    # Unable to introspect signature for value.
                    # It might be a built-in function that lacks signature support.
                    # Assume conservatively that value does NOT match the requested type.
                    return failure
                else:
                    sig_min_param_count = 0
                    sig_max_param_count = 0
                    for expected_param in sig.parameters.values():
                        if (
                            expected_param.kind == Parameter.POSITIONAL_ONLY
                            or expected_param.kind == Parameter.POSITIONAL_OR_KEYWORD
                        ):
                            if expected_param.default is Parameter.empty:
                                sig_min_param_count += 1
                            sig_max_param_count += 1
                        elif expected_param.kind == Parameter.VAR_POSITIONAL:
                            sig_max_param_count = math.inf

                    if sig_min_param_count <= len(param_types) <= sig_max_param_count:
                        return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
                    else:
                        return failure
            else:
                return failure

    if isinstance(tp, _GenericAlias):
        raise TypeNotSupportedError(
            f"trycast does not know how to recognize generic type "
            f"{type_repr(type_origin)}."
        )

    if _is_typed_dict(tp):  # T extends TypedDict
        if isinstance(value, Mapping):
            if options.eval:
                resolved_annotations = get_type_hints(  # does use eval()
                    tp
                )  # resolve ForwardRefs in tp.__annotations__
            else:
                resolved_annotations = tp.__annotations__  # type: ignore[attribute-error]  # pytype

            try:
                # {typing in Python 3.9+, typing_extensions}.TypedDict
                required_keys = tp.__required_keys__  # type: ignore[attribute-error]  # pytype
            except AttributeError:
                # {typing in Python 3.8, mypy_extensions}.TypedDict
                if options.strict:
                    if sys.version_info[:2] >= (3, 9):
                        advise = "Suggest use a typing.TypedDict instead."
                    else:
                        advise = "Suggest use a typing_extensions.TypedDict instead."
                    advise2 = "Or use trycast(..., strict=False)."
                    raise TypeNotSupportedError(
                        f"trycast cannot determine which keys are required "
                        f"and which are potentially-missing for the "
                        f"specified kind of TypedDict. {advise} {advise2}"
                    )
                else:
                    if tp.__total__:  # type: ignore[attribute-error]  # pytype
                        required_keys = resolved_annotations.keys()
                    else:
                        required_keys = frozenset()

            for (k, v) in value.items():  # type: ignore[attribute-error]  # pytype
                V = resolved_annotations.get(k, _MISSING)
                if (
                    V is not _MISSING
                    and _trycast_inner(V, v, _FAILURE, options) is _FAILURE
                ):
                    return failure

            for k in required_keys:
                if k not in value:  # type: ignore[unsupported-operands]  # pytype
                    return failure
            if isinstance(tp, type):
                return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
            else:
                return value
        else:
            return failure

    if _is_newtype(tp):
        if options.strict:
            supertype_repr = type_repr(tp.__supertype__)  # type: ignore[attribute-error]  # pytype
            raise TypeNotSupportedError(
                f"trycast cannot reliably determine whether value is "
                f"a NewType({tp.__name__!r}, {supertype_repr}) because "
                f"NewType wrappers are erased at runtime "
                f"and are indistinguishable from their supertype. "
                f"Consider using trycast(..., strict=False) to treat "
                f"NewType({tp.__name__!r}, {supertype_repr}) "
                f"like {supertype_repr}."
            )
        else:
            supertype = tp.__supertype__  # type: ignore[attribute-error]  # pytype
            return _trycast_inner(supertype, value, failure, options)

    if isinstance(tp, TypeVar):  # type: ignore[wrong-arg-types]  # pytype
        raise TypeNotSupportedError(
            "trycast cannot reliably determine whether value matches a TypeVar."
        )

    if tp is Any:
        if isinstance(tp, type):
            return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return value

    if tp is NoReturn:
        return failure

    if isinstance(tp, ForwardRef):
        raise UnresolvedForwardRefError()

    if isinstance(value, tp):  # type: ignore[wrong-arg-types]  # pytype
        return value
    else:
        return failure


class TypeNotSupportedError(TypeError):
    pass


class UnresolvedForwardRefError(TypeError):
    pass


@overload
def _trycast_listlike(
    tp: Type[_T],
    value: object,
    failure: _F,
    listlike_type: Type,
    options: _TrycastOptions,
    *,
    covariant_t: bool = False,
    t_ellipsis: bool = False,
) -> Union[_T, _F]:
    ...  # pragma: no cover


@overload
def _trycast_listlike(
    tp: object,
    value: object,
    failure: _F,
    listlike_type: Type,
    options: _TrycastOptions,
    *,
    covariant_t: bool = False,
    t_ellipsis: bool = False,
) -> Union[object, _F]:
    ...  # pragma: no cover


def _trycast_listlike(
    tp, value, failure, listlike_type, options, *, covariant_t=False, t_ellipsis=False
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
            for x in value:  # type: ignore[attribute-error]  # pytype
                if _trycast_inner(T, x, _FAILURE, options) is _FAILURE:
                    return failure

        if isinstance(tp, type):
            return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return value
    else:
        return failure


@overload
def _trycast_dictlike(
    tp: Type[_T],
    value: object,
    failure: _F,
    dictlike_type: Type,
    options: _TrycastOptions,
    *,
    covariant_v: bool = False,
) -> Union[_T, _F]:
    ...  # pragma: no cover


@overload
def _trycast_dictlike(
    tp: object,
    value: object,
    failure: _F,
    dictlike_type: Type,
    options: _TrycastOptions,
    *,
    covariant_v: bool = False,
) -> Union[object, _F]:
    ...  # pragma: no cover


def _trycast_dictlike(tp, value, failure, dictlike_type, options, *, covariant_v=False):
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
            for (k, v) in value.items():  # type: ignore[attribute-error]  # pytype
                if (
                    _trycast_inner(K, k, _FAILURE, options) is _FAILURE
                    or _trycast_inner(V, v, _FAILURE, options) is _FAILURE
                ):
                    return failure
        if isinstance(tp, type):
            return cast(_T, value)  # type: ignore[reportGeneralTypeIssues]  # pyright
        else:
            return value
    else:
        return failure


def _is_simple_typevar(T: object, covariant: bool = False) -> bool:
    return (
        isinstance(T, TypeVar)  # type: ignore[wrong-arg-types]  # pytype
        and T.__constraints__ == ()  # type: ignore[attribute-error]  # pytype
        and T.__covariant__ == covariant  # type: ignore[attribute-error]  # pytype
        and T.__contravariant__ is False  # type: ignore[attribute-error]  # pytype
        and T.__constraints__ == ()  # type: ignore[attribute-error]  # pytype
    )


# ------------------------------------------------------------------------------
# isassignable

# TODO: Once support for TypeForm is implemented in mypy,
#       replace the   `(Type[T]) -> TypeGuard[T]` overload
#       and the       `(object) -> bool` overload with
#       the following `(TypeForm[T]) -> TypeGuard[T]` overload:
#
#       See: https://github.com/python/mypy/issues/9773
# @overload
# def isassignable(value: object, tp: TypeForm[_T]) -> TypeGuard[_T]: ...


@overload
def isassignable(value: object, tp: str, *, eval: Literal[False]) -> NoReturn:
    ...  # pragma: no cover


@overload
def isassignable(value: object, tp: str, *, eval: bool = True) -> bool:
    ...  # pragma: no cover


@overload
def isassignable(value: object, tp: Type[_T], *, eval: bool = True) -> TypeGuard[_T]:  # type: ignore[invalid-annotation]  # pytype
    ...  # pragma: no cover


@overload
def isassignable(value: object, tp: object, *, eval: bool = True) -> bool:
    ...  # pragma: no cover


def isassignable(value, tp, *, eval=True):
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

    Parameters:
    * eval --
        If eval=False then isassignable will not attempt to resolve string
        type references, which requires the use of the eval() function.
        Otherwise string type references will be accepted.

    Raises:
    * TypeNotSupportedError --
        * If strict=True and either mypy_extensions.TypedDict or a
          Python 3.8 typing.TypedDict is found within the `tp` argument.
        * If strict=True and a NewType is found within the `tp` argument.
        * If a TypeVar is found within the `tp` argument.
        * If an unrecognized Generic type is found within the `tp` argument.
    * UnresolvedForwardRefError --
        If `tp` is a type form which contains a ForwardRef.
    * UnresolvableTypeError --
        If `tp` is a string that could not be resolved to a type.
    """
    if isinstance(tp, type):
        return cast(  # type: ignore[invalid-annotation]  # pytype
            TypeGuard[_T],  # type: ignore[not-indexable]  # pytype
            (
                trycast(tp, value, _isassignable_failure, strict=True, eval=eval)
                is not _isassignable_failure
            ),
        )
    else:
        return (
            trycast(tp, value, _isassignable_failure, strict=True, eval=eval)
            is not _isassignable_failure
        )


_isassignable_failure = object()


# ------------------------------------------------------------------------------
# eval_type_str

_IMPORTABLE_TYPE_EXPRESSION_RE = re.compile(r"^((?:[a-zA-Z0-9_]+\.)+)(.*)$")
_UNIMPORTABLE_TYPE_EXPRESSION_RE = re.compile(r"^[a-zA-Z0-9_]+(\[.*\])?$")
_BUILTINS_MODULE: ModuleType = builtins
_EXTRA_ADVISE_IF_MOD_IS_BUILTINS = (
    " Try altering the type argument to be a string "
    "reference (surrounded with quotes) instead, "
    "if not already done."
)


# TODO: Use this signature for _eval_type once support for TypeForm is
#       implemented in mypy. See: https://github.com/python/mypy/issues/9773
# def _eval_type(tp: str) -> TypeForm: ...


@functools.lru_cache()
def eval_type_str(tp: str) -> object:
    """
    Resolves a string-reference to a type that can be imported,
    such as `'typing.List'`.

    This function does internally cache lookups that have been made in
    the past to improve performance. If you need to clear this cache
    you can call:

        eval_type_str.cache_clear()

    Note that this function's implementation uses eval() internally.

    Raises:
    * UnresolvableTypeError --
        If the specified string-reference could not be resolved to a type.
    """
    if not isinstance(tp, str):  # pragma: no cover
        raise ValueError()

    # Determine which module to lookup the type from
    mod: ModuleType
    module_name: str
    member_expr: str
    m = _IMPORTABLE_TYPE_EXPRESSION_RE.fullmatch(tp)
    if m is not None:
        (module_name_dot, member_expr) = m.groups()
        module_name = module_name_dot[:-1]
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            raise UnresolvableTypeError(
                f"Could not resolve type {tp!r}: " f"Could not import {module_name!r}."
            )
    else:
        m = _UNIMPORTABLE_TYPE_EXPRESSION_RE.fullmatch(tp)
        if m is not None:
            mod = _BUILTINS_MODULE
            module_name = _BUILTINS_MODULE.__name__
            member_expr = tp
        else:
            raise UnresolvableTypeError(
                f"Could not resolve type {tp!r}: "
                f"{tp!r} does not appear to be a valid type."
            )

    # Lookup the type from a module
    try:
        member = eval(member_expr, mod.__dict__, None)
    except Exception:
        raise UnresolvableTypeError(
            f"Could not resolve type {tp!r}: "
            f"Could not eval {member_expr!r} inside module {module_name!r}."
            f"{_EXTRA_ADVISE_IF_MOD_IS_BUILTINS if mod is _BUILTINS_MODULE else ''}"
        )

    # Interpret an imported str as a TypeAlias
    if isinstance(member, str):
        member = ForwardRef(member, is_argument=False)

    # Resolve any ForwardRef instances inside the type
    try:
        member = eval_type(member, mod.__dict__, None)  # type: ignore[16]  # pyre
    except Exception:
        raise UnresolvableTypeError(
            f"Could not resolve type {tp!r}: "
            f"Could not eval type {member!r} inside module {module_name!r}."
            f"{_EXTRA_ADVISE_IF_MOD_IS_BUILTINS if mod is _BUILTINS_MODULE else ''}"
        )

    # 1. Ensure the object is actually a type
    # 2. As a special case, interpret None as type(None)
    try:
        member = _type_check(member, f"Could not resolve type {tp!r}: ")  # type: ignore[16]  # pyre
    except TypeError as e:
        raise UnresolvableTypeError(str(e))
    return member


class UnresolvableTypeError(TypeError):
    pass


# ------------------------------------------------------------------------------
