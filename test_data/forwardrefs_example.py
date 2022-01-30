import sys
from typing import Dict, List, Union

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


Scatterplot = List["Point2D"]  # forward reference


PointForLabel = Dict["str", "Point2D"]  # forward reference


Shape = Union["Circle", "Rect"]  # forward reference


class Rect(TypedDict):
    type: Literal["rect"]
    x: float
    y: float
    width: float
    height: float


class Circle(TypedDict):
    type: Literal["circle"]
    center: "Point2D"  # forward reference
    radius: float


class Point2D(TypedDict):
    x: float
    y: float
