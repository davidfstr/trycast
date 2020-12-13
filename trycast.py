from typing import cast, List, Literal, Optional, overload, Type, TypeVar, Union
from typing import _GenericAlias, _TypedDictMeta  # type: ignore  # private API not in stubs


__all__ = ['trycast']


_T = TypeVar('_T')
_F = TypeVar('_F')

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
    elif type is float:
        # 1. Accept ints as valid float values
        # 2. Do not accept bools as valid float values
        if isinstance(value, float) or (isinstance(value, int) and not isinstance(value, bool)):
            return cast(_T, value)
        else:
            return failure
    elif isinstance(type, _GenericAlias) and type.__origin__ is list:  # List, List[T]
        if isinstance(value, list):
            (T,) = type.__args__
            if _is_simple_typevar(T):
                pass
            else:
                for x in value:
                    if trycast(T, x, _FAILURE) is _FAILURE:
                        return failure
            return cast(_T, value)
        else:
            return failure
    elif isinstance(type, _GenericAlias) and type.__origin__ is dict:  # Dict, Dict[K, V]
        if isinstance(value, dict):
            (K, V) = type.__args__
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
    elif isinstance(type, _GenericAlias) and type.__origin__ is Union:  # Union[T1, T2, ...]
        for T in type.__args__:
            if trycast(T, value, _FAILURE) is not _FAILURE:
                return cast(_T, value)
        return failure
    elif isinstance(type, _GenericAlias) and type.__origin__ is Literal:  # Literal[...]
        for literal in type.__args__:
            if value == literal:
                return cast(_T, value)
        return failure
    elif isinstance(type, _TypedDictMeta):  # T extends TypedDict
        if isinstance(value, dict):
            if type.__total__ and len(value) != len(type.__annotations__):
                return failure
            for (k, V) in type.__annotations__.items():
                v = value.get(k, _MISSING)
                if v is _MISSING or trycast(V, v, _FAILURE) is _FAILURE:
                    return failure
            return cast(_T, value)
        else:
            return failure
    elif isinstance(type, tuple):
        raise TypeError(
            'trycast does not support checking against a tuple of types. '
            'Try checking against a Union[T1, T2, ...] instead.')
    else:
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
