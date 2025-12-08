from typing import Dict, List, Literal
from typing import TypedDict as RichTypedDict
from typing import Union


class Point2D(RichTypedDict):
    x: float
    y: float


PointForLabel = Dict[str, Point2D]


Scatterplot = List[Point2D]


class Rect(RichTypedDict):
    type: Literal["rect"]
    x: float
    y: float
    width: float
    height: float


class Circle(RichTypedDict):
    type: Literal["circle"]
    center: Point2D
    radius: float


Shape = Union[Circle, Rect]
