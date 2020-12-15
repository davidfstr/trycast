import os
import subprocess
import sys
from trycast import trycast
from tests_shape_example import (
    draw_shape_endpoint,
    HTTP_400_BAD_REQUEST,
    shapes_drawn,
)
from typing import Dict, List, Optional, Union
from unittest import skip, TestCase

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
        self.assertTryCastFailure(bool, '')
        self.assertTryCastFailure(bool, [])
        self.assertTryCastFailure(bool, {})
        self.assertTryCastFailure(bool, set())
        
        # Truthy values
        self.assertTryCastFailure(bool, 1)
        self.assertTryCastFailure(bool, 'foo')
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
        self.assertTryCastFailure(int, '0')
        self.assertTryCastFailure(int, '1')
        self.assertTryCastFailure(int, '-1')
        
        # non-ints
        self.assertTryCastFailure(int, 'foo')
        self.assertTryCastFailure(int, [1])
        self.assertTryCastFailure(int, {1: 1})
        self.assertTryCastFailure(int, {1})
        self.assertTryCastFailure(int, object())
    
    def test_float(self) -> None:
        # Actual floats, parsable by json.loads(...)
        self.assertTryCastSuccess(float, 0.0)
        self.assertTryCastSuccess(float, 0.5)
        self.assertTryCastSuccess(float, 1.0)
        self.assertTryCastSuccess(float, 2e+20)
        self.assertTryCastSuccess(float, 2e-20)
        
        # Actual floats, parsable by json.loads(..., allow_nan=True)
        self.assertTryCastSuccess(float, float('inf'))
        self.assertTryCastSuccess(float, float('-inf'))
        self.assertTryCastSuccess(float, float('nan'))
        
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
        self.assertTryCastFailure(float, '1.0')
        self.assertTryCastFailure(float, 'inf')
        self.assertTryCastFailure(float, 'Infinity')
        
        # int-like bools
        self.assertTryCastFailure(float, False)
        self.assertTryCastFailure(float, True)
        
        # int-like strs
        self.assertTryCastFailure(float, '0')
        self.assertTryCastFailure(float, '1')
        self.assertTryCastFailure(float, '-1')
        
        # non-floats
        self.assertTryCastFailure(float, 'foo')
        self.assertTryCastFailure(float, [1])
        self.assertTryCastFailure(float, {1: 1})
        self.assertTryCastFailure(float, {1})
        self.assertTryCastFailure(float, object())
        
        # non-ints
        self.assertTryCastFailure(float, 'foo')
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
        self.assertTryCastFailure(type(None), 'foo')
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
        self.assertTryCastFailure(list, (1,2))
        
        # list-like sets
        self.assertTryCastFailure(list, set())
        self.assertTryCastFailure(list, {1})
        self.assertTryCastFailure(list, {1,2})
        
        # non-lists
        self.assertTryCastFailure(list, 0)
        self.assertTryCastFailure(list, 'foo')
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
        self.assertTryCastFailure(List, (1,2))
        
        # list-like sets
        self.assertTryCastFailure(List, set())
        self.assertTryCastFailure(List, {1})
        self.assertTryCastFailure(List, {1,2})
        
        # non-lists
        self.assertTryCastFailure(List, 0)
        self.assertTryCastFailure(List, 'foo')
        self.assertTryCastFailure(List, {1: 1})
        self.assertTryCastFailure(List, {1})
        self.assertTryCastFailure(List, object())
    
    def test_dict(self) -> None:
        # Actual dict
        self.assertTryCastSuccess(dict, {})
        self.assertTryCastSuccess(dict, {1: 1})
        self.assertTryCastSuccess(dict, {'x': 1, 'y': 1})
        
        # non-dicts
        self.assertTryCastFailure(dict, 0)
        self.assertTryCastFailure(dict, 'foo')
        self.assertTryCastFailure(dict, [1])
        self.assertTryCastFailure(dict, {1})
        self.assertTryCastFailure(dict, object())
    
    def test_big_dict(self) -> None:
        # Actual dict
        self.assertTryCastSuccess(Dict, {})
        self.assertTryCastSuccess(Dict, {1: 1})
        self.assertTryCastSuccess(Dict, {'x': 1, 'y': 1})
        
        # non-dicts
        self.assertTryCastFailure(Dict, 0)
        self.assertTryCastFailure(Dict, 'foo')
        self.assertTryCastFailure(Dict, [1])
        self.assertTryCastFailure(Dict, {1})
        self.assertTryCastFailure(Dict, object())
    
    # === Generic Collections ===
    
    @skip('requires Python 3.9+ to implement')
    def test_list_t(self) -> None:
        pass
    
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
        self.assertTryCastFailure(List[int], 'foo')
        self.assertTryCastFailure(List[int], ['1'])
        self.assertTryCastFailure(List[int], {1: 1})
        self.assertTryCastFailure(List[int], {1})
        self.assertTryCastFailure(List[int], object())
    
    @skip('requires Python 3.9+ to implement')
    def test_dict_k_v(self) -> None:
        pass
    
    def test_big_dict_k_v(self) -> None:
        # Actual dict[K, V]
        self.assertTryCastSuccess(Dict[str, int], {})
        self.assertTryCastSuccess(Dict[str, int], {'x': 1})
        self.assertTryCastSuccess(Dict[str, int], {'x': 1, 'y': 2})
        
        # dict[K, V]-like dicts
        self.assertTryCastFailure(Dict[str, int], {'x': True})
        self.assertTryCastFailure(Dict[str, int], {'x': 1, 'y': True})
        
        # non-dict[K, V]s
        self.assertTryCastFailure(Dict[str, int], 0)
        self.assertTryCastFailure(Dict[str, int], 'foo')
        self.assertTryCastFailure(Dict[str, int], [1])
        self.assertTryCastFailure(Dict[str, int], {1: 1})
        self.assertTryCastFailure(Dict[str, int], {1})
        self.assertTryCastFailure(Dict[str, int], object())
    
    # === TypedDicts ===
    
    def test_typeddict(self) -> None:
        class Point2D(TypedDict):
            x: int
            y: int
        
        class Point2DPlus(TypedDict, total=False):
            x: int
            y: int
        
        class Point3D(TypedDict):
            x: int
            y: int
            z: int
        
        # Point2D
        self.assertTryCastSuccess(Point2D, {'x': 1, 'y': 1})
        self.assertTryCastFailure(Point2D, {'x': 1, 'y': 1, 'z': 1})
        
        # Point2DPlus
        self.assertTryCastSuccess(Point2DPlus, {'x': 1, 'y': 1})
        self.assertTryCastSuccess(Point2DPlus, {'x': 1, 'y': 1, 'z': 1})
        
        # Point3D
        self.assertTryCastFailure(Point3D, {'x': 1, 'y': 1})
        self.assertTryCastSuccess(Point3D, {'x': 1, 'y': 1, 'z': 1})
    
    # === Unions ===
    
    def test_union(self) -> None:
        # Union[int, str]
        self.assertTryCastSuccess(Union[int, str], 1)
        self.assertTryCastSuccess(Union[int, str], 'foo')
        
        # non-Union[int, str]
        self.assertTryCastFailure(Union[int, str], [])
    
    def test_optional(self) -> None:
        # Optional[str]
        self.assertTryCastNoneSuccess(Optional[str])
        self.assertTryCastSuccess(Optional[str], 'foo')
        
        # non-Optional[str]
        self.assertTryCastFailure(Optional[str], [])
    
    # === Literals ===
    
    def test_literal(self) -> None:
        # Literal
        self.assertTryCastSuccess(Literal['circle'], 'circle')
        self.assertTryCastSuccess(Literal[1], 1)
        self.assertTryCastSuccess(Literal[True], True)
        
        # Literal-like with the wrong value
        self.assertTryCastFailure(Literal['circle'], 'square')
        self.assertTryCastFailure(Literal[1], 2)
        self.assertTryCastFailure(Literal[True], False)
        
        # non-Literal
        self.assertTryCastFailure(Literal['circle'], 0)
        self.assertTryCastFailure(Literal['circle'], 'foo')
        self.assertTryCastFailure(Literal['circle'], [1])
        self.assertTryCastFailure(Literal['circle'], {1: 1})
        self.assertTryCastFailure(Literal['circle'], {1})
        self.assertTryCastFailure(Literal['circle'], object())
    
    # === Special ===
    
    def test_tuple_of_types(self) -> None:
        self.assertRaises(TypeError, lambda: trycast((int, str), 1))  # type: ignore
    
    # === Large Examples ===
    
    def text_shape_endpoint_parsing_example(self) -> None:
        x1 = dict(type='circle', center=dict(x=50, y=50), radius=25)
        xA = dict(type='circle', center=dict(x=50, y=50)           )
        x2 = dict(type='rect', x=10, y=20, width=50, height=50)
        xB = dict(type='rect',             width=50, height=50)
        xC = dict(type='oval', x=10, y=20, width=50, height=50)
        
        draw_shape_endpoint(x1)
        draw_shape_endpoint(xA)
        draw_shape_endpoint(x2)
        draw_shape_endpoint(xB)
        draw_shape_endpoint(xC)
        
        self.assertEqual([
            x1,
            HTTP_400_BAD_REQUEST,
            x2,
            HTTP_400_BAD_REQUEST,
            HTTP_400_BAD_REQUEST,
        ], shapes_drawn)
    
    # === Typecheck ===
    
    def test_no_typechecker_errors_exist(self) -> None:
        try:
            subprocess.check_output(
                ['mypy'],
                env={
                    'LANG': 'en_US.UTF-8',
                    'PATH': os.environ.get('PATH', '')
                },
                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.fail(f'Typechecking failed:\n\n{e.output.decode("utf-8").strip()}')
    
    # === Utility ===
    
    def assertTryCastSuccess(self, tp: object, value: object) -> None:
        self.assertIs(value, trycast(tp, value))
    
    def assertTryCastFailure(self, tp: object, value: object) -> None:
        self.assertIs(None, trycast(tp, value))
    
    def assertTryCastNoneSuccess(self, tp: object) -> None:
        self.assertIs(None, trycast(tp, None, _FAILURE))
