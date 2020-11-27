from trycast import FloatInt, trycast
from typing import Dict, List, Literal, Optional, TypedDict, Union
from unittest import skip, TestCase


_FAILURE = object()

class TestTryCast(TestCase):
    # === Scalars ===
    
    def test_bool(self) -> None:
        x: object
        
        # Actual bools
        self.assertIs(x := True, trycast(bool, x))
        self.assertIs(x := False, trycast(bool, x))
        
        # bool-like ints
        self.assertIs(None, trycast(bool, 0))
        self.assertIs(None, trycast(bool, 1))
        
        # Falsy values
        self.assertIs(None, trycast(bool, 0))
        self.assertIs(None, trycast(bool, ''))
        self.assertIs(None, trycast(bool, []))
        self.assertIs(None, trycast(bool, {}))
        self.assertIs(None, trycast(bool, set()))
        
        # Truthy values
        self.assertIs(None, trycast(bool, 1))
        self.assertIs(None, trycast(bool, 'foo'))
        self.assertIs(None, trycast(bool, [1]))
        self.assertIs(None, trycast(bool, {1: 1}))
        self.assertIs(None, trycast(bool, {1}))
        self.assertIs(None, trycast(bool, object()))
    
    def test_int(self) -> None:
        x: object
        
        # Actual ints
        self.assertIs(x := 0, trycast(int, x))
        self.assertIs(x := 1, trycast(int, x))
        self.assertIs(x := 2, trycast(int, x))
        self.assertIs(x := -1, trycast(int, x))
        self.assertIs(x := -2, trycast(int, x))
        
        # int-like bools
        self.assertIs(None, trycast(int, False))
        self.assertIs(None, trycast(int, True))
        
        # int-like floats
        self.assertIs(None, trycast(int, 0.0))
        self.assertIs(None, trycast(int, 1.0))
        self.assertIs(None, trycast(int, -1.0))
        
        # int-like strs
        self.assertIs(None, trycast(int, '0'))
        self.assertIs(None, trycast(int, '1'))
        self.assertIs(None, trycast(int, '-1'))
        
        # non-ints
        self.assertIs(None, trycast(int, 'foo'))
        self.assertIs(None, trycast(int, [1]))
        self.assertIs(None, trycast(int, {1: 1}))
        self.assertIs(None, trycast(int, {1}))
        self.assertIs(None, trycast(int, object()))
    
    def test_float(self) -> None:
        x: object
        
        # Actual floats, parsable by json.loads(...)
        self.assertIs(x := 0.0, trycast(float, x))
        self.assertIs(x := 0.5, trycast(float, x))
        self.assertIs(x := 1.0, trycast(float, x))
        self.assertIs(x := 2e+20, trycast(float, x))
        self.assertIs(x := 2e-20, trycast(float, x))
        
        # Actual floats, parsable by json.loads(..., allow_nan=True)
        self.assertIs(x := float('inf'), trycast(float, x))
        self.assertIs(x := float('-inf'), trycast(float, x))
        self.assertIs(x := float('nan'), trycast(float, x))
        
        # float-like ints
        self.assertIs(None, trycast(float, 0))
        self.assertIs(None, trycast(float, 1))
        self.assertIs(None, trycast(float, 2))
        
        # float-like bools
        self.assertIs(None, trycast(float, False))
        self.assertIs(None, trycast(float, True))
        
        # float-like strs
        self.assertIs(None, trycast(float, '1.0'))
        self.assertIs(None, trycast(float, 'inf'))
        self.assertIs(None, trycast(float, 'Infinity'))
        
        # non-floats
        self.assertIs(None, trycast(float, 0))
        self.assertIs(None, trycast(float, 'foo'))
        self.assertIs(None, trycast(float, [1]))
        self.assertIs(None, trycast(float, {1: 1}))
        self.assertIs(None, trycast(float, {1}))
        self.assertIs(None, trycast(float, object()))
    
    def test_floatint(self) -> None:
        x: object
        
        # Actual ints
        self.assertIs(x := 0, trycast(FloatInt, x))
        self.assertIs(x := 1, trycast(FloatInt, x))
        self.assertIs(x := 2, trycast(FloatInt, x))
        self.assertIs(x := -1, trycast(FloatInt, x))
        self.assertIs(x := -2, trycast(FloatInt, x))
        
        # Actual floats, parsable by json.loads(...)
        self.assertIs(x := 0.0, trycast(FloatInt, x))
        self.assertIs(x := 0.5, trycast(FloatInt, x))
        self.assertIs(x := 1.0, trycast(FloatInt, x))
        self.assertIs(x := 2e+20, trycast(FloatInt, x))
        self.assertIs(x := 2e-20, trycast(FloatInt, x))
        
        # Actual floats, parsable by json.loads(..., allow_nan=True)
        self.assertIs(x := float('inf'), trycast(FloatInt, x))
        self.assertIs(x := float('-inf'), trycast(FloatInt, x))
        self.assertIs(x := float('nan'), trycast(FloatInt, x))
        
        # int-like bools
        self.assertIs(None, trycast(FloatInt, False))
        self.assertIs(None, trycast(FloatInt, True))
        
        # int-like strs
        self.assertIs(None, trycast(FloatInt, '0'))
        self.assertIs(None, trycast(FloatInt, '1'))
        self.assertIs(None, trycast(FloatInt, '-1'))
        
        # float-like bools
        self.assertIs(None, trycast(FloatInt, False))
        self.assertIs(None, trycast(FloatInt, True))
        
        # float-like strs
        self.assertIs(None, trycast(FloatInt, '1.0'))
        self.assertIs(None, trycast(FloatInt, 'inf'))
        self.assertIs(None, trycast(FloatInt, 'Infinity'))
        
        # non-ints
        self.assertIs(None, trycast(FloatInt, 'foo'))
        self.assertIs(None, trycast(FloatInt, [1]))
        self.assertIs(None, trycast(FloatInt, {1: 1}))
        self.assertIs(None, trycast(FloatInt, {1}))
        self.assertIs(None, trycast(FloatInt, object()))
        
        # non-floats
        self.assertIs(None, trycast(FloatInt, 'foo'))
        self.assertIs(None, trycast(FloatInt, [1]))
        self.assertIs(None, trycast(FloatInt, {1: 1}))
        self.assertIs(None, trycast(FloatInt, {1}))
        self.assertIs(None, trycast(FloatInt, object()))
    
    def test_none(self) -> None:
        self.assertRaises(TypeError, lambda: trycast(None, None))  # type: ignore
    
    def test_none_type(self) -> None:
        x: object
        
        # Actual None
        self.assertIs(x := None, trycast(type(None), x, _FAILURE))
        
        # non-None
        self.assertIs(None, trycast(type(None), 0))
        self.assertIs(None, trycast(type(None), 'foo'))
        self.assertIs(None, trycast(type(None), [1]))
        self.assertIs(None, trycast(type(None), {1: 1}))
        self.assertIs(None, trycast(type(None), {1}))
        self.assertIs(None, trycast(type(None), object()))
    
    # === Raw Collections ===
    
    def test_list(self) -> None:
        x: object
        
        # Actual list
        self.assertIs(x := [], trycast(list, x))
        self.assertIs(x := [1], trycast(list, x))
        self.assertIs(x := [1, 2], trycast(list, x))
        
        # list-like tuples
        self.assertIs(None, trycast(list, ()))
        self.assertIs(None, trycast(list, (1,)))
        self.assertIs(None, trycast(list, (1,2)))
        
        # list-like sets
        self.assertIs(None, trycast(list, set()))
        self.assertIs(None, trycast(list, {1}))
        self.assertIs(None, trycast(list, {1,2}))
        
        # non-lists
        self.assertIs(None, trycast(list, 0))
        self.assertIs(None, trycast(list, 'foo'))
        self.assertIs(None, trycast(list, {1: 1}))
        self.assertIs(None, trycast(list, {1}))
        self.assertIs(None, trycast(list, object()))
    
    def test_big_list(self) -> None:
        x: object
        
        # Actual list
        self.assertIs(x := [], trycast(List, x))
        self.assertIs(x := [1], trycast(List, x))
        self.assertIs(x := [1, 2], trycast(List, x))
        
        # list-like tuples
        self.assertIs(None, trycast(List, ()))
        self.assertIs(None, trycast(List, (1,)))
        self.assertIs(None, trycast(List, (1,2)))
        
        # list-like sets
        self.assertIs(None, trycast(List, set()))
        self.assertIs(None, trycast(List, {1}))
        self.assertIs(None, trycast(List, {1,2}))
        
        # non-lists
        self.assertIs(None, trycast(List, 0))
        self.assertIs(None, trycast(List, 'foo'))
        self.assertIs(None, trycast(List, {1: 1}))
        self.assertIs(None, trycast(List, {1}))
        self.assertIs(None, trycast(List, object()))
    
    def test_dict(self) -> None:
        x: object
        
        # Actual dict
        self.assertIs(x := {}, trycast(dict, x))
        self.assertIs(x := {1: 1}, trycast(dict, x))
        self.assertIs(x := {'x': 1, 'y': 1}, trycast(dict, x))
        
        # non-dicts
        self.assertIs(None, trycast(dict, 0))
        self.assertIs(None, trycast(dict, 'foo'))
        self.assertIs(None, trycast(dict, [1]))
        self.assertIs(None, trycast(dict, {1}))
        self.assertIs(None, trycast(dict, object()))
    
    def test_big_dict(self) -> None:
        x: object
        
        # Actual dict
        self.assertIs(x := {}, trycast(Dict, x))
        self.assertIs(x := {1: 1}, trycast(Dict, x))
        self.assertIs(x := {'x': 1, 'y': 1}, trycast(Dict, x))
        
        # non-dicts
        self.assertIs(None, trycast(Dict, 0))
        self.assertIs(None, trycast(Dict, 'foo'))
        self.assertIs(None, trycast(Dict, [1]))
        self.assertIs(None, trycast(Dict, {1}))
        self.assertIs(None, trycast(Dict, object()))
    
    # === Generic Collections ===
    
    @skip('requires Python 3.9+ to implement')
    def test_list_t(self) -> None:
        pass
    
    def test_big_list_t(self) -> None:
        x: object
        
        # Actual list[T]
        self.assertIs(x := [], trycast(List[int], x))
        self.assertIs(x := [1], trycast(List[int], x))
        self.assertIs(x := [1, 2], trycast(List[int], x))
        
        # list[T]-like lists
        self.assertIs(None, trycast(List[int], [True]))
        self.assertIs(None, trycast(List[int], [1, True]))
        
        # non-list[T]s
        self.assertIs(None, trycast(List[int], 0))
        self.assertIs(None, trycast(List[int], 'foo'))
        self.assertIs(None, trycast(List[int], ['1']))
        self.assertIs(None, trycast(List[int], {1: 1}))
        self.assertIs(None, trycast(List[int], {1}))
        self.assertIs(None, trycast(List[int], object()))
    
    @skip('requires Python 3.9+ to implement')
    def test_dict_k_v(self) -> None:
        pass
    
    def test_big_dict_k_v(self) -> None:
        x: object
        
        # Actual dict[K, V]
        self.assertIs(x := {}, trycast(Dict[str, int], x))
        self.assertIs(x := {'x': 1}, trycast(Dict[str, int], x))
        self.assertIs(x := {'x': 1, 'y': 2}, trycast(Dict[str, int], x))
        
        # dict[K, V]-like dicts
        self.assertIs(None, trycast(Dict[str, int], {'x': True}))
        self.assertIs(None, trycast(Dict[str, int], {'x': 1, 'y': True}))
        
        # non-dict[K, V]s
        self.assertIs(None, trycast(Dict[str, int], 0))
        self.assertIs(None, trycast(Dict[str, int], 'foo'))
        self.assertIs(None, trycast(Dict[str, int], [1]))
        self.assertIs(None, trycast(Dict[str, int], {1: 1}))
        self.assertIs(None, trycast(Dict[str, int], {1}))
        self.assertIs(None, trycast(Dict[str, int], object()))
    
    # === TypedDicts ===
    
    def test_typeddict(self) -> None:
        x: object
        
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
        self.assertIs(x := {'x': 1, 'y': 1}, trycast(Point2D, x))
        self.assertIs(None, trycast(Point2D, {'x': 1, 'y': 1, 'z': 1}))
        
        # Point2DPlus
        self.assertIs(x := {'x': 1, 'y': 1}, trycast(Point2DPlus, x))
        self.assertIs(x := {'x': 1, 'y': 1, 'z': 1}, trycast(Point2DPlus, x))
        
        # Point3D
        self.assertIs(None, trycast(Point3D, {'x': 1, 'y': 1}))
        self.assertIs(x := {'x': 1, 'y': 1, 'z': 1}, trycast(Point3D, x))
    
    # === Unions ===
    
    def test_union(self) -> None:
        x: object
        
        # Union[int, str]
        self.assertIs(x := 1, trycast(Union[int, str], x))
        self.assertIs(x := 'foo', trycast(Union[int, str], x))
        
        # non-Union[int, str]
        self.assertIs(None, trycast(Union[int, str], []))
    
    def test_optional(self) -> None:
        x: object
        
        # Optional[str]
        self.assertIs(x := None, trycast(Optional[str], x, _FAILURE))
        self.assertIs(x := 'foo', trycast(Optional[str], x))
        
        # non-Optional[str]
        self.assertIs(None, trycast(Optional[str], []))
    
    # === Literals ===
    
    def test_literal(self) -> None:
        x: object
        
        # Literal
        self.assertIs(x := 'circle', trycast(Literal['circle'], x))
        self.assertIs(x := 1, trycast(Literal[1], x))
        self.assertIs(x := True, trycast(Literal[True], x))
        
        # Literal-like with the wrong value
        self.assertIs(None, trycast(Literal['circle'], 'square'))
        self.assertIs(None, trycast(Literal[1], 2))
        self.assertIs(None, trycast(Literal[True], False))
        
        # non-Literal
        self.assertIs(None, trycast(Literal['circle'], 0))
        self.assertIs(None, trycast(Literal['circle'], 'foo'))
        self.assertIs(None, trycast(Literal['circle'], [1]))
        self.assertIs(None, trycast(Literal['circle'], {1: 1}))
        self.assertIs(None, trycast(Literal['circle'], {1}))
        self.assertIs(None, trycast(Literal['circle'], object()))
    
    # === Large Examples ===
    
    def text_shape_endpoint_parsing_example(self) -> None:
        class Point2D(TypedDict):
            x: float
            y: float
        
        class Circle(TypedDict):
            type: Literal['circle']
            center: Point2D  # has a nested TypedDict!
            radius: float
        
        class Rect(TypedDict):
            type: Literal['rect']
            x: float
            y: float
            width: float
            height: float
        
        Shape = Union[Circle, Rect]  # a Tagged Union
        
        shapes_drawn = []  # type: List[Union[Shape, ValueError]]
        
        HTTP_400_BAD_REQUEST = ValueError('HTTP 400: Bad Request')
        
        def draw_shape_endpoint(request_json: object) -> None:
            shape = trycast(Shape, request_json)  # type: Optional[Shape]
            if shape is not None:
                draw_shape(shape)
            else:
                shapes_drawn.append(HTTP_400_BAD_REQUEST)
        
        def draw_shape(shape: Shape) -> None:
            shapes_drawn.append(shape)
        
        draw_shape_endpoint(x1 := dict(type='circle', center=dict(x=50, y=50), radius=25))
        draw_shape_endpoint(      dict(type='circle', center=dict(x=50, y=50)           ))
        draw_shape_endpoint(x2 := dict(type='rect', x=10, y=20, width=50, height=50))
        draw_shape_endpoint(      dict(type='rect',             width=50, height=50))
        draw_shape_endpoint(      dict(type='oval', x=10, y=20, width=50, height=50))
        self.assertEqual([
            x1,
            HTTP_400_BAD_REQUEST,
            x2,
            HTTP_400_BAD_REQUEST,
            HTTP_400_BAD_REQUEST,
        ], shapes_drawn)
