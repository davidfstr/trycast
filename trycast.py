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
    Literal,
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
from typing import cast, get_args, get_origin, overload

# GenericAlias
if sys.version_info >= (3, 9):
    from types import GenericAlias
else:

    class GenericAlias(type):  # type: ignore[no-redef]
        __origin__: object
        __args__: Tuple[object, ...]

        def __init__(self, origin: object, args: Tuple[object, ...]) -> None: ...

        ...


# UnionType
if sys.version_info >= (3, 10):
    from types import UnionType  # type: ignore[attr-defined]
else:

    class UnionType(type):  # type: ignore[no-redef]
        ...


# Never
if sys.version_info >= (3, 11):
    from typing import Never
else:

    class Never(type):  # type: ignore[no-redef]
        ...


# TypeAliasType
if sys.version_info >= (3, 12):
    from typing import TypeAliasType  # type: ignore[21]  # pyre
else:

    class TypeAliasType(type):  # type: ignore[no-redef]
        __type_params__: Tuple[object, ...]
        __value__: object
        ...


# get_type_hints
try:
    # If typing_extensions available,
    # understands both typing.* and typing_extensions.* types
    from typing_extensions import get_type_hints  # type: ignore[attr-defined]
except ImportError:
    # If typing_extensions not available
    from typing import (  # type: ignore[misc, assignment]  # incompatible import
        get_type_hints,
    )


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
    # Python 3.8 - 3.9
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
    # NOTE: This function is derived from Python 3.12's typing._type_check
    #       internal helper function. It is however more concerned with
    #       rejecting known non-types (true negatives) than it is
    #       avoiding rejecting actual types (false negatives).
    #       See discussion at: https://github.com/python/cpython/issues/92601
    def _type_check(arg: object, msg: str):
        """Returns the argument if it appears to be a type.
        Raises TypeError if the argument is a known non-type.

        As a special case, accepts None and returns type(None) instead.
        Also wraps strings into ForwardRef instances.
        """
        arg = _type_convert(arg, module=None)
        # Recognize *common* non-types. (This check is not exhaustive.)
        if isinstance(arg, (dict, list, int, tuple)):
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
    "checkcast",
    "isassignable",
    # NOTE: May be part of the API in the future
    # "eval_type_str",
)


_T = TypeVar("_T")
_F = TypeVar("_F")
_SimpleTypeVar = TypeVar("_SimpleTypeVar")
_SimpleTypeVarCo = TypeVar("_SimpleTypeVarCo", covariant=True)  # type: ignore[not-supported-yet]  # pytest

_MISSING = object()

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


# Overload: (tp: str, eval: Literal[False]) -> NoReturn


@overload
def trycast(  # type: ignore[43]  # pyre
    tp: str, value: object, /, *, strict: bool = True, eval: Literal[False]
) -> NoReturn: ...  # pragma: no cover


# Overload Group: (tp: str|Type[_T]|object, value: object) -> ...


@overload
def trycast(tp: str, value: object, /, *, strict: bool = True, eval: bool = True) -> bool:  # type: ignore[43]  # pyre
    ...  # pragma: no cover


@overload
def trycast(  # type: ignore[43]  # pyre
    tp: Type[_T], value: object, /, *, strict: bool = True, eval: bool = True
) -> Optional[_T]: ...  # pragma: no cover


@overload
def trycast(  # type: ignore[43]  # pyre
    tp: object, value: object, /, *, strict: bool = True, eval: bool = True
) -> Optional[object]: ...  # pragma: no cover


# Overload Group: (tp: str|Type[_T]|object, value: object, failure: object) -> ...


@overload
def trycast(
    tp: str,
    value: object,
    /,
    failure: object,
    *,
    strict: bool = True,
    eval: Literal[False],
) -> NoReturn: ...  # pragma: no cover


@overload
def trycast(
    tp: Type[_T],
    value: object,
    /,
    failure: _F,
    *,
    strict: bool = True,
    eval: bool = True,
) -> Union[_T, _F]: ...  # pragma: no cover


@overload
def trycast(
    tp: object, value: object, /, failure: _F, *, strict: bool = True, eval: bool = True
) -> Union[object, _F]: ...  # pragma: no cover


# Implementation


def trycast(tp, value, /, failure=None, *, strict=True, eval=True):
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
    * eval --
        If eval=False then this function will not attempt to resolve string
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
    e = _checkcast_outer(tp, value, _TrycastOptions(strict, eval, funcname="trycast"))
    if e is not None:
        return failure  # type: ignore[bad-return-type]  # pytype
    else:
        return value  # type: ignore[bad-return-type]  # pytype


# ------------------------------------------------------------------------------
# checkcast

# TODO: Once support for TypeForm is implemented in mypy,
#       replace the   `(Type[T]) -> Optional[T]` overload
#       and the       `(object) -> Optional[object]` overload with
#       the following `(TypeForm[T]) -> Optional[T]` overload:
#
#       See: https://github.com/python/mypy/issues/9773
# @overload
# def checkcast(tp: TypeForm[_T], value: object) -> Optional[_T]: ...


# Overload: (tp: str, eval: Literal[False]) -> NoReturn


@overload
def checkcast(  # type: ignore[43]  # pyre
    tp: str,
    value: object,
    /,
    *,
    strict: bool = True,
    eval: Literal[False],
    _funcname: str = "checkcast",
) -> NoReturn: ...  # pragma: no cover


# Overload Group: (tp: str|Type[_T]|object, value: object) -> ...


@overload
def checkcast(tp: str, value: object, /, *, strict: bool = True, eval: bool = True, _funcname: str = "checkcast") -> bool:  # type: ignore[43]  # pyre
    ...  # pragma: no cover


@overload
def checkcast(  # type: ignore[43]  # pyre
    tp: Type[_T],
    value: object,
    /,
    *,
    strict: bool = True,
    eval: bool = True,
    _funcname: str = "checkcast",
) -> Optional[_T]: ...  # pragma: no cover


@overload
def checkcast(  # type: ignore[43]  # pyre
    tp: object,
    value: object,
    /,
    *,
    strict: bool = True,
    eval: bool = True,
    _funcname: str = "checkcast",
) -> Optional[object]: ...  # pragma: no cover


# Implementation


def checkcast(tp, value, /, *, strict=True, eval=True, _funcname="checkcast"):
    """
    If `value` is in the shape of `tp` (as accepted by a Python typechecker
    conforming to PEP 484 "Type Hints") then returns it, otherwise
    raises ValidationError

    This method logically performs an operation similar to:

        if isinstance(tp, value):
            return value
        else:
            raise ValidationError(tp, value)

    except that it supports many more types than `isinstance`, including:
        * List[T]
        * Dict[K, V]
        * Optional[T]
        * Union[T1, T2, ...]
        * Literal[...]
        * T extends TypedDict

    See trycast.trycast() for information about parameters,
    raised exceptions, and other details.

    Raises:
    * ValidationError -- If `value` is not in the shape of `tp`.
    * TypeNotSupportedError
    * UnresolvedForwardRefError
    * UnresolvableTypeError
    """
    e = _checkcast_outer(tp, value, _TrycastOptions(strict, eval, _funcname))
    if e is not None:
        raise e
    else:
        return value  # type: ignore[bad-return-type]  # pytype


class _TrycastOptions(NamedTuple):
    strict: bool
    eval: bool
    funcname: str


def _checkcast_outer(
    tp: object, value: object, options: _TrycastOptions
) -> "Optional[ValidationError]":
    if isinstance(tp, str):
        if options.eval:  # == options.eval (for pytype)
            tp = eval_type_str(tp)  # does use eval()
        else:
            raise UnresolvableTypeError(
                f"Could not resolve type {tp!r}: "
                f"Type appears to be a string reference "
                f"and {options.funcname}() was called with eval=False, "
                f"disabling eval of string type references."
            )
    else:
        try:
            # TODO: Eliminate format operation done by f-string
            #       from the hot path of _checkcast_outer()
            tp = _type_check(  # type: ignore[16]  # pyre
                tp,
                f"{options.funcname}() requires a type as its first argument.",
            )
        except TypeError:
            if isinstance(tp, tuple) and len(tp) >= 1 and isinstance(tp[0], type):
                raise TypeError(
                    f"{options.funcname} does not support checking against a tuple of types. "
                    "Try checking against a Union[T1, T2, ...] instead."
                )
            else:
                raise
    try:
        return _checkcast_inner(tp, value, options)  # type: ignore[bad-return-type]  # pytype
    except UnresolvedForwardRefError:
        if options.eval:
            advise = (
                "Try altering the first type argument to be a string "
                "reference (surrounded with quotes) instead."
            )
        else:
            advise = (
                f"{options.funcname}() cannot resolve string type references "
                "because it was called with eval=False."
            )
        raise UnresolvedForwardRefError(
            f"{options.funcname} does not support checking against type form {tp!r} "
            "which contains a string-based forward reference. "
            f"{advise}"
        )


def _checkcast_inner(
    tp: object, value: object, options: _TrycastOptions
) -> "Optional[ValidationError]":
    """
    Raises:
    * TypeNotSupportedError
    * UnresolvedForwardRefError
    """
    if tp is int:
        # Also accept bools as valid int values
        if isinstance(value, int):
            return None
        else:
            return ValidationError(tp, value)

    if tp is float:
        # Also accept ints and bools as valid float values
        if isinstance(value, float) or isinstance(value, int):
            return None
        else:
            return ValidationError(tp, value)

    if tp is complex:
        # Also accept floats, ints, and bools as valid complex values
        if (
            isinstance(value, complex)
            or isinstance(value, float)
            or isinstance(value, int)
        ):
            return None
        else:
            return ValidationError(tp, value)

    type_origin = get_origin(tp)

    if type_origin is list or type_origin is List:  # List, List[T]
        return _checkcast_listlike(tp, value, list, options)

    if type_origin is set or type_origin is Set:  # Set, Set[T]
        return _checkcast_listlike(tp, value, set, options)

    if type_origin is frozenset or type_origin is FrozenSet:  # FrozenSet, FrozenSet[T]
        return _checkcast_listlike(tp, value, frozenset, options, covariant_t=True)

    if type_origin is tuple or type_origin is Tuple:
        if isinstance(value, tuple):
            type_args = get_args(tp)

            if len(type_args) == 0 or (
                len(type_args) == 2 and type_args[1] is Ellipsis
            ):  # Tuple, Tuple[T, ...]

                return _checkcast_listlike(
                    tp,
                    value,
                    tuple,
                    options,
                    covariant_t=True,
                    t_ellipsis=True,
                )
            else:  # Tuple[Ts]
                if len(value) != len(type_args):
                    return ValidationError(tp, value)

                for i, T, t in zip(range(len(type_args)), type_args, value):
                    e = _checkcast_inner(T, t, options)
                    if e is not None:
                        return ValidationError(
                            tp,
                            value,
                            _causes=[e._with_prefix(_LazyStr(lambda: f"At index {i}"))],
                        )

                return None
        else:
            return ValidationError(tp, value)

    if type_origin is Sequence or type_origin is CSequence:  # Sequence, Sequence[T]
        return _checkcast_listlike(tp, value, CSequence, options, covariant_t=True)

    if (
        type_origin is MutableSequence or type_origin is CMutableSequence
    ):  # MutableSequence, MutableSequence[T]
        return _checkcast_listlike(tp, value, CMutableSequence, options)

    if type_origin is dict or type_origin is Dict:  # Dict, Dict[K, V]
        return _checkcast_dictlike(tp, value, dict, options)

    if type_origin is Mapping or type_origin is CMapping:  # Mapping, Mapping[K, V]
        return _checkcast_dictlike(tp, value, CMapping, options, covariant_v=True)

    if (
        type_origin is MutableMapping or type_origin is CMutableMapping
    ):  # MutableMapping, MutableMapping[K, V]
        return _checkcast_dictlike(tp, value, CMutableMapping, options)

    if (
        type_origin is Union or type_origin is UnionType
    ):  # Union[T1, T2, ...], Optional[T]
        causes = []
        for T in get_args(tp):
            e = _checkcast_inner(T, value, options)
            if e is not None:
                causes.append(e)
            else:
                return None
        return ValidationError(tp, value, _causes=causes)

    if type_origin is Literal:  # Literal[...]
        for literal in get_args(tp):
            if value == literal:
                return None
        return ValidationError(tp, value)

    if type_origin is CCallable:
        callable_args = get_args(tp)
        if callable_args == ():
            # Callable
            if callable(value):
                return None
            else:
                return ValidationError(tp, value)
        else:
            assert len(callable_args) == 2
            (param_types, return_type) = callable_args

            if return_type is not Any:
                # Callable[..., T]
                raise TypeNotSupportedError(
                    f"{options.funcname} cannot reliably determine whether value is "
                    f"a {type_repr(tp)} because "
                    f"callables at runtime do not always have a "
                    f"declared return type. "
                    f"Consider using {options.funcname}(Callable, value) instead."
                )

            if param_types is Ellipsis:
                # Callable[..., Any]
                return _checkcast_inner(Callable, value, options)

            assert isinstance(param_types, list)
            for param_type in param_types:
                if param_type is not Any:
                    raise TypeNotSupportedError(
                        f"{options.funcname} cannot reliably determine whether value is "
                        f"a {type_repr(tp)} because "
                        f"callables at runtime do not always have "
                        f"declared parameter types. "
                        f"Consider using {options.funcname}("
                        f"Callable[{','.join('Any' * len(param_types))}, Any], value) "
                        f"instead."
                    )

            # Callable[[Any * N], Any]
            if callable(value):
                try:
                    sig = _inspect_signature(value)
                except TypeError:
                    # Not a callable
                    return ValidationError(tp, value)
                except ValueError as f:
                    # Unable to introspect signature for value.
                    # It might be a built-in function that lacks signature support.
                    # Assume conservatively that value does NOT match the requested type.
                    e = ValidationError(tp, value)
                    e.__cause__ = f
                    return e
                else:
                    sig_min_param_count = 0  # type: float
                    sig_max_param_count = 0  # type: float
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
                        return None
                    else:
                        return ValidationError(tp, value)
            else:
                return ValidationError(tp, value)

    if isinstance(type_origin, TypeAliasType):  # type: ignore[16]  # pyre
        if len(type_origin.__type_params__) > 0:
            substitutions = dict(
                zip(
                    type_origin.__type_params__,
                    get_args(tp) + ((Any,) * len(type_origin.__type_params__)),
                )
            )  # type: Dict[object, object]
            new_tp = _substitute(tp.__value__, substitutions)  # type: ignore[attr-defined]  # mypy
        else:
            new_tp = tp.__value__  # type: ignore[attr-defined]  # mypy
        return _checkcast_inner(new_tp, value, options)  # type: ignore[16]  # pyre

    if isinstance(tp, _GenericAlias):  # type: ignore[16]  # pyre
        raise TypeNotSupportedError(
            f"{options.funcname} does not know how to recognize generic type "
            f"{type_repr(type_origin)}."
        )

    if _is_typed_dict(tp):  # T extends TypedDict
        if isinstance(value, Mapping):
            if options.eval:
                resolved_annotations = get_type_hints(  # does use eval()
                    tp  # type: ignore[arg-type]  # mypy
                )  # resolve ForwardRefs in tp.__annotations__
            else:
                resolved_annotations = tp.__annotations__  # type: ignore[attribute-error]  # pytype

            try:
                # {typing in Python 3.9+, typing_extensions}.TypedDict
                required_keys = tp.__required_keys__  # type: ignore[attr-defined, attribute-error]  # mypy, pytype
            except AttributeError:
                # {typing in Python 3.8, mypy_extensions}.TypedDict
                if options.strict:
                    if sys.version_info[:2] >= (3, 9):
                        advise = "Suggest use a typing.TypedDict instead."
                    else:
                        advise = "Suggest use a typing_extensions.TypedDict instead."
                    advise2 = f"Or use {options.funcname}(..., strict=False)."
                    raise TypeNotSupportedError(
                        f"{options.funcname} cannot determine which keys are required "
                        f"and which are potentially-missing for the "
                        f"specified kind of TypedDict. {advise} {advise2}"
                    )
                else:
                    if tp.__total__:  # type: ignore[attr-defined, attribute-error]  # mypy, pytype
                        required_keys = resolved_annotations.keys()
                    else:
                        required_keys = frozenset()

            for k, v in value.items():  # type: ignore[attribute-error]  # pytype
                V = resolved_annotations.get(k, _MISSING)
                if V is not _MISSING:
                    e = _checkcast_inner(V, v, options)
                    if e is not None:
                        return ValidationError(
                            tp,
                            value,
                            _causes=[e._with_prefix(_LazyStr(lambda: f"At key {k!r}"))],
                        )

            for k in required_keys:
                if k not in value:  # type: ignore[unsupported-operands]  # pytype
                    return ValidationError(
                        tp,
                        value,
                        _causes=[
                            ValidationError._from_message(
                                _LazyStr(lambda: f"Required key {k!r} is missing")
                            )
                        ],
                    )
            return None
        else:
            return ValidationError(tp, value)

    if _is_newtype(tp):
        if options.strict:
            supertype_repr = type_repr(tp.__supertype__)  # type: ignore[attr-defined, attribute-error]  # mypy, pytype
            tp_name_repr = repr(tp.__name__)  # type: ignore[attr-defined]  # mypy
            raise TypeNotSupportedError(
                f"{options.funcname} cannot reliably determine whether value is "
                f"a NewType({tp_name_repr}, {supertype_repr}) because "
                f"NewType wrappers are erased at runtime "
                f"and are indistinguishable from their supertype. "
                f"Consider using {options.funcname}(..., strict=False) to treat "
                f"NewType({tp_name_repr}, {supertype_repr}) "
                f"like {supertype_repr}."
            )
        else:
            supertype = tp.__supertype__  # type: ignore[attr-defined, attribute-error]  # mypy, pytype
            return _checkcast_inner(supertype, value, options)

    if isinstance(tp, TypeVar):  # type: ignore[wrong-arg-types]  # pytype
        raise TypeNotSupportedError(
            f"{options.funcname} cannot reliably determine whether value matches a TypeVar."
        )

    if tp is Any:
        return None

    if tp is Never or tp is NoReturn:
        return ValidationError(tp, value)

    if isinstance(tp, TypeAliasType):  # type: ignore[16]  # pyre
        if len(tp.__type_params__) > 0:  # type: ignore[16]  # pyre
            substitutions = dict(
                zip(tp.__type_params__, ((Any,) * len(tp.__type_params__)))
            )
            new_tp = _substitute(tp.__value__, substitutions)
        else:
            new_tp = tp.__value__
        return _checkcast_inner(new_tp, value, options)  # type: ignore[16]  # pyre

    if isinstance(tp, ForwardRef):
        raise UnresolvedForwardRefError()

    if isinstance(value, tp):  # type: ignore[arg-type, wrong-arg-types]  # mypy, pytype
        return None
    else:
        return ValidationError(tp, value)


class TypeNotSupportedError(TypeError):
    pass


class UnresolvedForwardRefError(TypeError):
    pass


def _substitute(tp: object, substitutions: Dict[object, object]) -> object:
    if isinstance(tp, GenericAlias):  # ex: tuple[T1, T2]
        return GenericAlias(  # type: ignore[reportCallIssue]  # pyright
            tp.__origin__, tuple([_substitute(a, substitutions) for a in tp.__args__])
        )
    if isinstance(tp, TypeVar):  # type: ignore[wrong-arg-types]  # pytype
        return substitutions.get(tp, tp)
    return tp


def _checkcast_listlike(
    tp: object,
    value: object,
    listlike_type: Type,
    options: _TrycastOptions,
    *,
    covariant_t: bool = False,
    t_ellipsis: bool = False,
) -> "Optional[ValidationError]":
    if isinstance(value, listlike_type):
        T_ = get_args(tp)

        if len(T_) == 0:  # Python 3.9+
            (T,) = (_SimpleTypeVarCo if covariant_t else _SimpleTypeVar,)

        else:
            if t_ellipsis:
                if len(T_) == 2 and T_[1] is Ellipsis:
                    (T, _) = T_
                else:
                    return ValidationError(tp, value)
            else:
                (T,) = T_

        if _is_simple_typevar(T, covariant=covariant_t):
            pass
        else:
            for i, x in enumerate(value):  # type: ignore[attribute-error]  # pytype
                e = _checkcast_inner(T, x, options)
                if e is not None:
                    return ValidationError(
                        tp,
                        value,
                        _causes=[e._with_prefix(_LazyStr(lambda: f"At index {i}"))],
                    )

        return None
    else:
        return ValidationError(tp, value)


def _checkcast_dictlike(
    tp: object,
    value: object,
    dictlike_type: Type,
    options: _TrycastOptions,
    *,
    covariant_v: bool = False,
) -> "Optional[ValidationError]":
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
            for k, v in value.items():  # type: ignore[attribute-error]  # pytype
                e = _checkcast_inner(K, k, options)
                if e is not None:
                    return ValidationError(
                        tp,
                        value,
                        _causes=[e._with_prefix(_LazyStr(lambda: f"Key {k!r}"))],
                    )
                e = _checkcast_inner(V, v, options)
                if e is not None:
                    return ValidationError(
                        tp,
                        value,
                        _causes=[e._with_prefix(_LazyStr(lambda: f"At key {k!r}"))],
                    )
        return None
    else:
        return ValidationError(tp, value)


def _is_simple_typevar(T: object, covariant: bool = False) -> bool:
    return (
        isinstance(T, TypeVar)  # type: ignore[wrong-arg-types]  # pytype
        and T.__constraints__ == ()  # type: ignore[attribute-error]  # pytype
        and T.__covariant__ == covariant  # type: ignore[attribute-error]  # pytype
        and T.__contravariant__ is False  # type: ignore[attribute-error]  # pytype
        and T.__constraints__ == ()  # type: ignore[attribute-error]  # pytype
    )


# ------------------------------------------------------------------------------
# ValidationError


if sys.version_info >= (3, 11):
    from typing import Self as _SelfValidationError
else:
    _SelfValidationError = TypeVar("_SelfValidationError", bound="ValidationError")


class ValidationError(ValueError):
    # === Init ===

    def __init__(
        self,
        tp: object,
        value: object,
        /,
        # NOTE: Inner type and structure for representing "cause" information
        #       is private and may change in the future.
        _causes: "Optional[Sequence[ValidationError]]" = None,
        *,
        _message: "Optional[_LazyStr]" = None,
    ) -> None:
        """
        Creates a ValidationError related to the specified value not matching
        the expected specified type.

        Parameters (positional-only):
        * tp -- the expected type of the specified value.
        * value -- a value.
        """
        if _causes is None:
            _causes = []
        if _message is None:
            _message = _LazyStr(
                lambda: f"Expected {format_type_str(tp)} but found {value!r}"
            )
        super().__init__(_message)
        self._tp = tp
        self._value = value
        self._causes = _causes
        self._prefix = None  # type: Optional[_LazyStr]

    # Private factory method
    @staticmethod
    def _from_message(message: "_LazyStr") -> "ValidationError":
        return ValidationError(None, None, _message=message)

    # Private builder method
    def _with_prefix(
        self: _SelfValidationError, prefix: "_LazyStr", /  # type: ignore[11]  # pyre  # noqa: W504
    ) -> _SelfValidationError:
        self._prefix = prefix
        return self

    # === __str__ ===

    def __str__(self) -> str:
        """
        Returns a human-readable explanation of this ValidationError.

        The specific format of this explanation may change in the future.
        """
        parts = []  # type: List[str]
        self._format_to(parts)
        return "".join(parts)

    def _format_to(self, parts: List[str], indent: int = 0) -> None:
        for i in range(indent):
            parts.append("  ")
        if self._prefix is not None:
            parts.append(str(self._prefix))  # NOTE: May be a _LazyStr
            parts.append(": ")
        parts.append(super().__str__())
        if len(self._causes) > 0:
            for c in self._causes:  # type: ignore[16]  # pyre
                parts.append("\n")
                c._format_to(parts, indent=indent + 1)


class _LazyStr(str):
    def __init__(self, value_func: Callable[[], str], /) -> None:
        self._value_func = value_func
        self._value = None  # type: Optional[str]

    def __str__(self) -> str:
        if self._value is None:
            self._value = self._value_func()
        return self._value


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
def isassignable(
    value: object, tp: str, /, *, eval: Literal[False]
) -> NoReturn: ...  # pragma: no cover


@overload
def isassignable(
    value: object, tp: str, /, *, eval: bool = True
) -> bool: ...  # pragma: no cover


@overload
def isassignable(value: object, tp: Type[_T], /, *, eval: bool = True) -> TypeGuard[_T]:  # type: ignore[invalid-annotation]  # pytype
    ...  # pragma: no cover


@overload
def isassignable(
    value: object, tp: object, /, *, eval: bool = True
) -> bool: ...  # pragma: no cover


def isassignable(value, tp, /, *, eval=True):
    """
    Returns whether `value` is in the shape of `tp`
    (as accepted by a Python typechecker conforming to PEP 484 "Type Hints").

    This method logically performs an operation similar to:

        return isinstance(value, tp)

    except that it supports many more types than `isinstance`, including:
        * List[T]
        * Dict[K, V]
        * Optional[T]
        * Union[T1, T2, ...]
        * Literal[...]
        * T extends TypedDict

    See trycast.trycast(..., strict=True) for information about parameters,
    raised exceptions, and other details.
    """
    e = _checkcast_outer(
        tp, value, _TrycastOptions(strict=True, eval=eval, funcname="isassignable")
    )
    result = e is None
    if isinstance(tp, type):
        return cast(  # type: ignore[invalid-annotation]  # pytype
            TypeGuard[_T],  # type: ignore[not-indexable]  # pytype
            result,
        )
    else:
        return result  # type: ignore[bad-return-type]  # pytype


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
def eval_type_str(tp: str, /) -> object:
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
# format_type_str


def format_type_str(tp: object, /) -> str:
    """
    Formats a type annotation object as a string similar to how it would
    appear in source code.
    """
    if tp is Ellipsis:
        return "..."

    tp_origin = get_origin(tp)
    if tp_origin is not None:
        tp_args = get_args(tp)
        if tp_args != ():
            if tp_origin is UnionType:
                return " | ".join([format_type_str(x) for x in tp_args])
            return (
                format_type_str(tp_origin)
                + "["
                + ", ".join([format_type_str(x) for x in tp_args])
                + "]"
            )
        tp_name = getattr(tp_origin, "__name__", None)
    else:
        tp_name = getattr(tp, "__name__", None)
    if tp_name is not None:
        return tp_name
    return repr(tp)


# ------------------------------------------------------------------------------
