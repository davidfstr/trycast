import sys
from typing import (
    cast, Dict, get_type_hints,
    List, Optional, overload, Tuple, TYPE_CHECKING, Type, TypeVar, Union,
)

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
        from typing_extensions import _Literal  # type: ignore  # private API not in stubs
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
    raise ImportError('Expected Python 3.6 or later.')


# _is_typed_dict
_typed_dict_meta_list = []
try:
    from typing import _TypedDictMeta as _TypingTypedDictMeta  # type: ignore  # private API not in stubs
    _typed_dict_meta_list.append(_TypingTypedDictMeta)
except ImportError:
    pass
try:
    from typing_extensions import _TypedDictMeta as _TypingExtensionsTypedDictMeta  # type: ignore  # private API not in stubs
    _typed_dict_meta_list.append(_TypingExtensionsTypedDictMeta)
except ImportError:
    pass
try:
    from mypy_extensions import _TypedDictMeta as _MypyExtensionsTypedDictMeta  # type: ignore  # private API not in stubs
    _typed_dict_meta_list.append(_MypyExtensionsTypedDictMeta)
except ImportError:
    pass
_typed_dict_metas = tuple(_typed_dict_meta_list)
def _is_typed_dict(tp: object) -> bool:
    return isinstance(tp, tuple(_typed_dict_metas))


__all__ = ['trycast']


_T = TypeVar('_T')
_F = TypeVar('_F')
_SimpleTypeVar = TypeVar('_SimpleTypeVar')

_MISSING = object()
_FAILURE = object()


# TODO: Use this signature for trycast once support for TypeForm is 
#       implemented in mypy.
#@overload
#def trycast(type: TypeForm[_T], value: object) -> Optional[_T]: ...
#@overload
#def trycast(type: TypeForm[_T], value: object, failure: _F) -> Union[_T, _F]: ...

@overload
def trycast(type: object, value: object) -> Optional[object]: ...
@overload
def trycast(type: object, value: object, failure: _F) -> Union[object, _F]: ...

def trycast(type, value, failure=None):
    """
    If `value` is in the shape of `type` (as accepted by a Python typechecker
    conforming to PEP 484 "Type Hints") then returns it, otherwise returns
    `failure` (which is None by default).
    
    This method logically performs an operation similar to:
    
        return value if isinstance(type, value) else failure
    
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
    """
    if type is int:
        # Do not accept bools as valid int values
        if isinstance(value, int) and not isinstance(value, bool):
            return cast(_T, value)
        else:
            return failure
    if type is float:
        # 1. Accept ints as valid float values
        # 2. Do not accept bools as valid float values
        if isinstance(value, float) or (isinstance(value, int) and not isinstance(value, bool)):
            return cast(_T, value)
        else:
            return failure
    
    type_origin = get_origin(type)
    if type_origin is list or type_origin is List:  # List, List[T]
        if isinstance(value, list):
            T_ = get_args(type)
            if len(T_) == 0:  # Python 3.9+
                (T,) = (_SimpleTypeVar,)
            else:
                (T,) = T_
            if _is_simple_typevar(T):
                pass
            else:
                for x in value:
                    if trycast(T, x, _FAILURE) is _FAILURE:
                        return failure
            return cast(_T, value)
        else:
            return failure
    if type_origin is dict or type_origin is Dict:  # Dict, Dict[K, V]
        if isinstance(value, dict):
            K_V = get_args(type)
            if len(K_V) == 0:  # Python 3.9+
                (K, V) = (_SimpleTypeVar, _SimpleTypeVar)
            else:
                (K, V) = K_V
            if _is_simple_typevar(K) and _is_simple_typevar(V):
                pass
            else:
                for (k, v) in value.items():
                    if trycast(K, k, _FAILURE) is _FAILURE or \
                            trycast(V, v, _FAILURE) is _FAILURE:
                        return failure
            return cast(_T, value)
        else:
            return failure
    if type_origin is Union:  # Union[T1, T2, ...]
        for T in get_args(type):
            if trycast(T, value, _FAILURE) is not _FAILURE:
                return cast(_T, value)
        return failure
    if type_origin is Literal:  # Literal[...]
        for literal in get_args(type):
            if value == literal:
                return cast(_T, value)
        return failure
    
    if _is_typed_dict(type):  # T extends TypedDict
        if isinstance(value, dict):
            resolved_annotations = get_type_hints(type)  # resolve ForwardRefs in type.__annotations__
            try:
                # {typing in Python 3.9+, typing_extensions}.TypedDict
                required_keys = type.__required_keys__
            except AttributeError:
                # {typing in Python 3.8, mypy_extensions}.TypedDict
                if type.__total__:
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
    
    if isinstance(type, tuple):
        raise TypeError(
            'trycast does not support checking against a tuple of types. '
            'Try checking against a Union[T1, T2, ...] instead.')
    
    if isinstance(value, type):  # type: ignore
        return value
    else:
        return failure


def _is_simple_typevar(T: object) -> bool:
    return (
        isinstance(T, TypeVar) and
        T.__constraints__ == () and
        T.__covariant__ == False and
        T.__contravariant__ == False and
        T.__constraints__ == ()
    )
